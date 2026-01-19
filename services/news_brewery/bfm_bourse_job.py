import re
import json
import time
import random
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st
from openai import OpenAI
from playwright.sync_api import sync_playwright

from services.raw_storage.raw_news_service import enrich_raw_items, insert_raw_news
from prompts.news_brewery.clean_dom_v1 import PROMPT_CLEAN_DOM_V1
from prompts.news_brewery.clean_dom_v2 import PROMPT_CLEAN_DOM_V2
from prompts.news_brewery.rewrite import PROMPT_REWRITE
from prompts.news_brewery.structure import PROMPT_STRUCTURE
from prompts.news_brewery.deduplicate import PROMPT_DEDUPLICATE
from prompts.news_brewery.jsonfy import PROMPT_JSONFY
from prompts.news_brewery.json_secure import PROMPT_JSON_SECURE


REQUEST_TIMEOUT = 60
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


@dataclass
class JobConfig:
    entry_url: str
    mode: str  # "today" or "last_hours"
    hours_window: int
    max_articles_total: int
    max_articles_per_bulletin: int
    scroll_min_px: int
    scroll_max_px: int
    min_page_time: int
    max_page_time: int
    wait_min_action: float
    wait_max_action: float
    shuffle_urls: bool
    clean_dom_agent: str
    fallback_agent: str
    output_language: str
    dry_run: bool
    max_consecutive_errors: int
    global_timeout_minutes: int
    pause_on_captcha: bool
    remove_buffer_after_success: bool
    headless: bool


class BfmBourseJob:
    def __init__(self) -> None:
        self.state = "idle"
        self.status_log: List[str] = []
        self.errors: List[str] = []
        self.processed = 0
        self.skipped = 0
        self.consecutive_errors = 0
        self.buffer_path: Optional[str] = None
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
        self.consecutive_errors = 0
        self.state = "running"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        if self.state == "running":
            self.state = "paused"
            self._pause_event.clear()
            self.status_log.append("⏸️ Job en pause")

    def resume(self) -> None:
        if self.state == "paused":
            self.state = "running"
            self._pause_event.set()
            self.status_log.append("▶️ Job repris")

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.set()
        if self.state in ("running", "paused"):
            self.state = "stopped"
            self.status_log.append("⏹️ Job stoppé")

    def get_status(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": self.errors,
            "status_log": self.status_log,
            "buffer_path": self.buffer_path,
        }

    def _wait_if_paused(self) -> None:
        while not self._pause_event.is_set():
            if self._stop_event.is_set():
                return
            time.sleep(0.5)

    def _sleep_random(self, min_value: float, max_value: float) -> None:
        wait_s = random.uniform(min_value, max_value)
        time.sleep(wait_s)

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

    def _is_captcha_or_wall(self, html: str) -> bool:
        text = html.lower()
        keywords = [
            "captcha",
            "robot",
            "abonne",
            "abonnement",
            "connectez-vous",
            "se connecter",
            "paywall",
        ]
        return any(k in text for k in keywords)

    def _parse_time_label(self, text: str) -> Optional[datetime]:
        time_match = re.search(r"\b(\d{1,2})h(\d{2})\b", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            now = datetime.now()
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        date_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text)
        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3))
            if year < 100:
                year += 2000
            return datetime(year, month, day)
        month_match = re.search(
            r"\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s*(\d{4})?\b",
            text,
            re.IGNORECASE,
        )
        if month_match:
            day = int(month_match.group(1))
            month_name = month_match.group(2).lower()
            year = int(month_match.group(3)) if month_match.group(3) else datetime.now().year
            months = {
                "janvier": 1,
                "février": 2,
                "fevrier": 2,
                "mars": 3,
                "avril": 4,
                "mai": 5,
                "juin": 6,
                "juillet": 7,
                "août": 8,
                "aout": 8,
                "septembre": 9,
                "octobre": 10,
                "novembre": 11,
                "décembre": 12,
                "decembre": 12,
            }
            month = months.get(month_name)
            if month:
                return datetime(year, month, day)
        return None

    def _within_window(self, label_dt: Optional[datetime], config: JobConfig) -> bool:
        if label_dt is None:
            return True
        now = datetime.now()
        if config.mode == "today":
            return label_dt.date() == now.date()
        if config.mode == "last_hours":
            return now - label_dt <= timedelta(hours=config.hours_window)
        return True

    def _collect_article_urls(self, page, config: JobConfig) -> List[Dict[str, str]]:
        try:
            page.get_by_role("link", name=re.compile(r"^tout$", re.I)).click(timeout=2000)
            self._sleep_random(config.wait_min_action, config.wait_max_action)
        except Exception:
            pass

        raw_items = page.eval_on_selector_all(
            ".wrapper-news-list .item",
            """els => els.map(el => {
                const timeEl = el.querySelector(".meta-date");
                const linkEl = el.querySelector(".title a");
                const timeText = timeEl ? (timeEl.textContent || "").trim() : "";
                const href = linkEl ? (linkEl.getAttribute("href") || "") : "";
                const title = linkEl ? (linkEl.textContent || "").trim() : "";
                return {timeText, href, title};
            })"""
        )

        results = []
        seen = set()
        for item in raw_items:
            href = (item.get("href", "") or "").strip()
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.tradingsat.com{href}"
            if "tradingsat.com/actualites" not in href and "/actualites/" not in href:
                continue
            if href.rstrip("/") == config.entry_url.rstrip("/"):
                continue
            if href in seen:
                continue
            seen.add(href)
            label_dt = self._parse_time_label(item.get("timeText", ""))
            if not self._within_window(label_dt, config):
                continue
            results.append({
                "url": href,
                "title": item.get("title", ""),
                "label_dt": label_dt.isoformat() if label_dt else "",
            })
            if len(results) >= config.max_articles_total:
                break
        return results

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
        buffer_path = f"/tmp/bfm_buffer_{datetime.now().strftime('%Y%m%d')}.txt"
        self.buffer_path = buffer_path
        self.status_log.append("🚀 Job démarré")

        try:
            with sync_playwright() as p:
                self.status_log.append("🧭 Lancement navigateur")
                browser = p.chromium.launch(headless=config.headless)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(60000)

                self.status_log.append("🌐 Ouverture page actualités")
                page.goto(config.entry_url, wait_until="domcontentloaded", timeout=60000)
                self._sleep_random(config.wait_min_action, config.wait_max_action)

                articles = self._collect_article_urls(page, config)
                if config.shuffle_urls:
                    random.shuffle(articles)

                self.status_log.append(f"🔎 {len(articles)} URL(s) détectée(s)")

                for idx, article in enumerate(articles, start=1):
                    if self._stop_event.is_set():
                        break
                    self._wait_if_paused()
                    if self._stop_event.is_set():
                        break

                    if time.time() - start_time > config.global_timeout_minutes * 60:
                        self.state = "failed"
                        self.errors.append("Timeout global atteint")
                        break

                    url = article.get("url", "")
                    self.status_log.append(f"➡️ Article {idx}/{len(articles)}")
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    except Exception as exc:
                        self.errors.append(f"Erreur navigation: {exc}")
                        self.consecutive_errors += 1
                        if self.consecutive_errors >= config.max_consecutive_errors:
                            self.state = "failed"
                            break
                        continue

                    self._sleep_random(config.wait_min_action, config.wait_max_action)

                    html = page.content()
                    if self._is_captcha_or_wall(html):
                        msg = f"Captcha/wall détecté: {url}"
                        self.errors.append(msg)
                        self.status_log.append(f"⚠️ {msg}")
                        if config.pause_on_captcha:
                            self.state = "paused"
                            self._pause_event.clear()
                            self._wait_if_paused()
                            if self._stop_event.is_set():
                                break
                        else:
                            self.skipped += 1
                            continue

                    scrolls = random.randint(1, 3)
                    for _ in range(scrolls):
                        scroll_px = random.randint(config.scroll_min_px, config.scroll_max_px)
                        page.mouse.wheel(0, scroll_px)
                        self._sleep_random(config.wait_min_action, config.wait_max_action)

                    self._sleep_random(config.min_page_time, config.max_page_time)

                    html = page.content()

                    cleaned = self._run_text_prompt(PROMPT_CLEAN_DOM_V1, html, temperature=0)
                    if not cleaned.strip():
                        cleaned = self._run_text_prompt(PROMPT_CLEAN_DOM_V2, html, temperature=0)

                    if not cleaned.strip():
                        self.errors.append("Clean DOM vide")
                        self.skipped += 1
                        continue

                    rewritten = self._run_text_prompt(PROMPT_REWRITE, cleaned, temperature=0.2)
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

                context.close()
                browser.close()
        except Exception as exc:
            self.state = "failed"
            self.errors.append(f"Erreur job: {exc}")
            self.status_log.append(f"❌ Job failed: {exc}")
            return

        if self.state in ("failed", "stopped"):
            return

        try:
            with open(buffer_path, "r", encoding="utf-8") as f:
                buffer_text = f.read()
        except Exception as exc:
            self.state = "failed"
            self.errors.append(f"Buffer introuvable: {exc}")
            return

        structured_text = self._extract_structured_text(buffer_text)
        deduped = self._deduplicate_blocks(structured_text)
        deduped = self._limit_blocks(deduped, config.max_articles_per_bulletin)

        json_result = self._jsonfy(deduped)
        if json_result.get("status") != "success":
            self.state = "failed"
            self.errors.append(json_result.get("message", "Erreur JSON"))
            return

        if config.dry_run:
            self.state = "completed"
        else:
            items = json_result.get("items", [])
            enriched = enrich_raw_items(
                items,
                flow="news_brewery",
                source_type="news",
                source_name="BFM Bourse",
                source_link=config.entry_url,
                source_date=datetime.now().isoformat(),
                source_raw=None,
            )
            result = insert_raw_news(enriched)
            if result.get("status") != "success":
                self.state = "failed"
                self.errors.append(result.get("message", "Erreur DB"))
                return
            self.state = "completed"

        if config.remove_buffer_after_success:
            try:
                import os
                os.remove(buffer_path)
            except Exception:
                pass


_JOB_INSTANCE: Optional[BfmBourseJob] = None


def get_bfm_job() -> BfmBourseJob:
    global _JOB_INSTANCE
    if _JOB_INSTANCE is None:
        _JOB_INSTANCE = BfmBourseJob()
    return _JOB_INSTANCE
