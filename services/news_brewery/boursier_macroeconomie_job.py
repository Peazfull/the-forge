import json
import time
import random
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from openai import OpenAI

from services.raw_storage.raw_news_service import enrich_raw_items, insert_raw_news
from services.hand_brewery.firecrawl_client import fetch_url_text
from services.news_brewery.rss_utils import (
    fetch_boursier_macroeconomie_dom_items,
    fetch_rss_items,
    merge_article_items,
)
from prompts.news_brewery.rewrite import PROMPT_REWRITE
from prompts.news_brewery.structure import PROMPT_STRUCTURE
from prompts.news_brewery.deduplicate import PROMPT_DEDUPLICATE
from prompts.news_brewery.jsonfy import PROMPT_JSONFY
from prompts.news_brewery.json_secure import PROMPT_JSON_SECURE


REQUEST_TIMEOUT = 60
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def _should_use_rss(feed_url: str) -> bool:
    return "rss" in (feed_url or "").lower() or (feed_url or "").lower().endswith(".xml")


@dataclass
class JobConfig:
    entry_url: str
    mode: str  # "today" or "last_hours"
    hours_window: int
    max_articles_total: int
    max_articles_per_bulletin: int
    wait_min_action: float
    wait_max_action: float
    shuffle_urls: bool
    dry_run: bool
    max_consecutive_errors: int
    global_timeout_minutes: int
    remove_buffer_after_success: bool
    use_rss: bool
    rss_feed_url: str
    rss_ignore_time_filter: bool
    rss_use_dom_fallback: bool
    use_firecrawl: bool
    urls_override: Optional[List[Dict[str, str]]]


class BoursierMacroeconomieJob:
    def __init__(self) -> None:
        self.state = "idle"
        self.status_log: List[str] = []
        self.errors: List[str] = []
        self.processed = 0
        self.skipped = 0
        self.total = 0
        self.current_index = 0
        self.started_at: Optional[float] = None
        self.last_log: str = ""
        self.consecutive_errors = 0
        self.buffer_path: Optional[str] = None
        self.buffer_text: str = ""
        self.json_preview_text: str = ""
        self.json_items: List[Dict[str, object]] = []
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._config: Optional[JobConfig] = None

    def start(self, config: JobConfig) -> None:
        if self.state == "running":
            return
        self._config = config
        self._stop_event.clear()
        self._pause_event.set()
        self.errors = []
        self.status_log = []
        self.processed = 0
        self.skipped = 0
        self.total = 0
        self.current_index = 0
        self.started_at = time.time()
        self.last_log = ""
        self.consecutive_errors = 0
        self.state = "running"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.set()
        if self.state in ("running", "paused"):
            self.state = "stopped"
            self._log("⏹️ Job stoppé")

    def clear(self) -> None:
        self._stop_event.set()
        self._pause_event.set()
        self.state = "idle"
        self.errors = []
        self.status_log = []
        self.processed = 0
        self.skipped = 0
        self.total = 0
        self.current_index = 0
        self.started_at = None
        self.last_log = ""
        self.buffer_path = None
        self.buffer_text = ""
        self.json_preview_text = ""
        self.json_items = []

    def get_status(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "processed": self.processed,
            "skipped": self.skipped,
            "total": self.total,
            "current_index": self.current_index,
            "started_at": self.started_at,
            "last_log": self.last_log,
            "errors": self.errors,
            "status_log": self.status_log,
            "buffer_path": self.buffer_path,
            "buffer_text": self.buffer_text,
            "json_preview_text": self.json_preview_text,
        }

    def set_buffer_text(self, text: str) -> None:
        self.buffer_text = text or ""

    def finalize_buffer(self) -> Dict[str, object]:
        if not self.buffer_text.strip():
            return {"status": "error", "message": "Buffer vide"}
        structured_text = self._extract_structured_text(self.buffer_text)
        limited_text = self._limit_blocks(structured_text, self._config.max_articles_per_bulletin if self._config else 0)
        json_result = self._jsonfy(limited_text)
        if json_result.get("status") != "success":
            return {"status": "error", "message": json_result.get("message", "Erreur JSON")}
        self.json_items = json_result.get("items", [])
        self.json_preview_text = json.dumps({"items": self.json_items}, indent=2, ensure_ascii=False)
        return {"status": "success", "items": self.json_items}

    def send_to_db(self) -> Dict[str, object]:
        if not self.json_items:
            return {"status": "error", "message": "Aucun item à insérer"}
        if self._config and self._config.dry_run:
            return {"status": "error", "message": "DRY RUN actif"}
        enriched = enrich_raw_items(
            self.json_items,
            flow="news_brewery",
            source_type="news",
            source_name="Boursier Macroeconomie",
            source_link=self._config.entry_url if self._config else "",
            source_date=datetime.now().isoformat(),
            source_raw=None,
        )
        result = insert_raw_news(enriched)
        if result.get("status") == "success":
            self.state = "completed"
            if self._config and self._config.remove_buffer_after_success and self.buffer_path:
                try:
                    import os
                    os.remove(self.buffer_path)
                except Exception:
                    pass
        return result

    def _wait_if_paused(self) -> None:
        while not self._pause_event.is_set():
            if self._stop_event.is_set():
                return
            time.sleep(0.5)

    def _sleep_random(self, min_value: float, max_value: float) -> None:
        wait_s = random.uniform(min_value, max_value)
        time.sleep(wait_s)

    def _log(self, message: str) -> None:
        self.last_log = message
        self.status_log.append(message)

    def _run_text_prompt(self, prompt: str, content: str, temperature: float = 0.2) -> str:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
            temperature=temperature,
            timeout=REQUEST_TIMEOUT,
        )
        return response.choices[0].message.content or ""

    def _format_buffer_block(self, article: Dict[str, str], content: str) -> str:
        return (
            "=== ARTICLE ===\n"
            f"URL: {article.get('url','')}\n"
            f"Date: {article.get('label_dt','')}\n"
            f"Title: {article.get('title','')}\n"
            "\n"
            f"{content.strip()}\n"
        )

    def _deduplicate_blocks(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._run_text_prompt(PROMPT_DEDUPLICATE, text, temperature=0.1).strip()

    def _limit_blocks(self, text: str, limit: int) -> str:
        if limit <= 0:
            return text
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        return "\n\n".join(blocks[:limit])

    def _extract_structured_text(self, buffer_text: str) -> str:
        blocks = [b.strip() for b in buffer_text.split("=== ARTICLE ===") if b.strip()]
        contents = []
        for block in blocks:
            parts = block.split("\n\n", 1)
            if len(parts) < 2:
                continue
            contents.append(parts[1].strip())
        return "\n\n".join(contents)

    def _jsonfy(self, text: str) -> Dict[str, object]:
        if not text.strip():
            return {"status": "error", "message": "Texte vide", "items": []}
        try:
            response_jsonfy = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PROMPT_JSONFY},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                timeout=REQUEST_TIMEOUT,
            )
            raw_json = response_jsonfy.choices[0].message.content or ""
            response_secure = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PROMPT_JSON_SECURE},
                    {"role": "user", "content": raw_json},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                timeout=REQUEST_TIMEOUT,
            )
            secure_json = response_secure.choices[0].message.content or ""
            data = json.loads(secure_json)
            return {"status": "success", "items": data.get("items", [])}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "items": []}

    def _run(self) -> None:
        config = self._config
        if not config:
            self.state = "failed"
            return
        start_time = time.time()
        buffer_path = f"/tmp/boursier_macroeconomie_buffer_{datetime.now().strftime('%Y%m%d')}.txt"
        self.buffer_path = buffer_path
        self.buffer_text = ""
        self.json_preview_text = ""
        self.json_items = []
        try:
            with open(buffer_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
        self._log("🚀 Job démarré")

        if not config.use_rss:
            self.errors.append("Mode RSS/DOM requis pour Boursier Macroeconomie")
            self.state = "failed"
            return

        try:
            self._log("📰 Mode RSS/DOM activé")
            if config.urls_override:
                articles = config.urls_override
            else:
                if _should_use_rss(config.rss_feed_url):
                    articles_rss = fetch_rss_items(
                        feed_url=config.rss_feed_url,
                        max_items=config.max_articles_total,
                        mode=config.mode,
                        hours_window=config.hours_window,
                        ignore_time_filter=config.rss_ignore_time_filter,
                    )
                else:
                    articles_rss = []
                if config.rss_use_dom_fallback:
                    articles_dom = fetch_boursier_macroeconomie_dom_items(
                        page_url=config.entry_url,
                        max_items=config.max_articles_total,
                        mode=config.mode,
                        hours_window=config.hours_window,
                        use_firecrawl_fallback=config.use_firecrawl,
                    )
                    if articles_dom:
                        self._log(f"🧩 DOM: {len(articles_dom)} URL(s) détectée(s)")
                    articles = merge_article_items(
                        articles_dom,
                        articles_rss,
                        config.max_articles_total,
                    )
                else:
                    articles = articles_rss
            if config.shuffle_urls:
                random.shuffle(articles)
            self.total = len(articles)
            self._log(f"🔎 {len(articles)} URL(s) détectée(s)")
            if self.total == 0:
                self.state = "failed"
                self.errors.append(
                    "Aucune URL détectée. DOM vide ou bloqué ; "
                    "active Firecrawl ou renseigne un RSS valide."
                )
                return

            for idx, article in enumerate(articles, start=1):
                if self._stop_event.is_set():
                    break
                self._wait_if_paused()
                if self._stop_event.is_set():
                    break
                self.current_index = idx

                if time.time() - start_time > config.global_timeout_minutes * 60:
                    self.state = "failed"
                    self.errors.append("Timeout global atteint")
                    break

                url = article.get("url", "")
                self._log(f"➡️ Article {idx}/{len(articles)}")

                if not config.use_firecrawl:
                    self.errors.append("Firecrawl désactivé, impossible de récupérer l'article")
                    self.skipped += 1
                    continue

                try:
                    raw_text = fetch_url_text(url)
                except Exception as exc:
                    self.errors.append(f"Firecrawl error: {exc}")
                    self.skipped += 1
                    continue

                # AI pipeline: rewrite -> structure (Clean DOM supprimé - Firecrawl suffit).
                rewritten = self._run_text_prompt(PROMPT_REWRITE, raw_text, temperature=0.2)
                if not rewritten.strip():
                    self.errors.append("Rewrite vide")
                    self.skipped += 1
                    continue

                structured = self._run_text_prompt(PROMPT_STRUCTURE, rewritten, temperature=0.2)
                if not structured.strip():
                    self.errors.append("Structure vide")
                    self.skipped += 1
                    continue

                with open(buffer_path, "a", encoding="utf-8") as f:
                    f.write(self._format_buffer_block(article, structured))
                    f.write("\n\n")

                self.processed += 1
                self.consecutive_errors = 0
                self._log(f"✅ Article {idx} terminé")

        except Exception as exc:
            self.state = "failed"
            self.errors.append(f"Erreur job: {exc}")
            self._log(f"❌ Job failed: {exc}")
            return

        if self.state in ("failed", "stopped"):
            return

        try:
            with open(buffer_path, "r", encoding="utf-8") as f:
                self.buffer_text = f.read()
        except Exception as exc:
            self.state = "failed"
            self.errors.append(f"Buffer introuvable: {exc}")
            return

        self.state = "ready"


_JOB_INSTANCE: Optional[BoursierMacroeconomieJob] = None


def get_boursier_macroeconomie_job() -> BoursierMacroeconomieJob:
    global _JOB_INSTANCE
    if _JOB_INSTANCE is None:
        _JOB_INSTANCE = BoursierMacroeconomieJob()
    return _JOB_INSTANCE
