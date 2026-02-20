import json
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st
from openai import OpenAI

from services.raw_storage.raw_news_service import enrich_raw_items, insert_raw_news
from services.hand_brewery.firecrawl_client import fetch_url_text
from prompts.news_brewery.deduplicate import PROMPT_DEDUPLICATE
from prompts.news_brewery.jsonfy import PROMPT_JSONFY
from prompts.news_brewery.json_secure import PROMPT_JSON_SECURE
from prompts.news_brewery.structure import PROMPT_STRUCTURE


REQUEST_TIMEOUT = 60
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


@dataclass
class MegaJobConfig:
    source_name: str
    source_link: str
    remove_buffer_after_success: bool
    dry_run: bool
    batch_size: int = 5
    firecrawl_concurrency: int = 3


class MegaJob:
    def __init__(self) -> None:
        self.state = "idle"  # idle, running, completed, failed
        self.buffer_text: str = ""
        self.json_preview_text: str = ""
        self.json_items: List[Dict[str, object]] = []
        self._config: Optional[MegaJobConfig] = None
        
        # Progress tracking
        self.total = 0
        self.current_index = 0
        self.processed = 0
        self.skipped = 0
        self.errors: List[str] = []
        self.status_log: List[str] = []
        self.last_log: str = ""
        self.started_at: Optional[float] = None
        
        # Threading
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._urls_to_scrape: List[Dict[str, str]] = []

    def set_config(self, config: MegaJobConfig) -> None:
        self._config = config

    def set_buffer_text(self, text: str) -> None:
        self.buffer_text = text or ""
    
    def start_auto_scraping(self, urls: List[Dict[str, str]]) -> None:
        """Lance le scraping automatisé de toutes les URLs avec pipeline complet"""
        if self.state == "running":
            return
        
        self._urls_to_scrape = urls
        self.total = len(urls)
        self.current_index = 0
        self.processed = 0
        self.skipped = 0
        self.errors = []
        self.status_log = []
        self.last_log = ""
        self.buffer_text = ""
        self.json_items = []
        self.json_preview_text = ""
        self.state = "running"
        self.started_at = time.time()
        self._stop_event.clear()
        
        self._thread = threading.Thread(target=self._run_auto_scraping, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        self._stop_event.set()
        if self.state == "running":
            self.state = "stopped"
            self._log("⏹️ Job stoppé")
    
    def get_status(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "total": self.total,
            "current_index": self.current_index,
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": self.errors,
            "status_log": self.status_log,
            "last_log": self.last_log,
            "buffer_text": self.buffer_text,
            "json_preview_text": self.json_preview_text,
            "json_items": self.json_items,
        }

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
    
    def _run_auto_scraping(self) -> None:
        """Boucle principale de scraping automatisé avec batches."""
        batch_size = int(getattr(self._config, "batch_size", 5) or 5) if self._config else 5
        batch_size = max(1, min(batch_size, 50))
        firecrawl_workers = int(getattr(self._config, "firecrawl_concurrency", 3) or 3) if self._config else 3
        firecrawl_workers = max(1, min(firecrawl_workers, 10))

        total_batches = (self.total + batch_size - 1) // batch_size
        total_inserted = 0
        
        self._log(
            f"🚀 Démarrage Mega Job - {self.total} URLs en {total_batches} batch(s) "
            f"de {batch_size} (Firecrawl x{firecrawl_workers})"
        )
        
        # Diviser en batches
        for batch_num in range(total_batches):
            if self._stop_event.is_set():
                break
            
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, self.total)
            batch_urls = self._urls_to_scrape[start_idx:end_idx]
            batch_size = len(batch_urls)
            
            self._log(f"📦 Batch {batch_num + 1}/{total_batches} - {batch_size} URLs")
            
            # Buffer pour ce batch
            batch_buffer = ""
            batch_processed = 0

            # Étape 1: Firecrawl (parallèle intra-batch)
            def _fetch_one(idx_in_batch: int, item: Dict[str, str]) -> Dict[str, object]:
                url = item.get("url", "") or ""
                source_label = item.get("source_label", "Unknown") or "Unknown"
                global_idx = start_idx + idx_in_batch
                try:
                    raw_text = fetch_url_text(url)
                    return {
                        "ok": True,
                        "global_idx": global_idx,
                        "idx_in_batch": idx_in_batch,
                        "source_label": source_label,
                        "url": url,
                        "raw_text": raw_text,
                    }
                except Exception as e:
                    return {
                        "ok": False,
                        "global_idx": global_idx,
                        "idx_in_batch": idx_in_batch,
                        "source_label": source_label,
                        "url": url,
                        "error": str(e),
                    }

            self._log(f"  🔥 Firecrawl batch (x{firecrawl_workers})…")
            fetch_results: List[Dict[str, object]] = []
            with ThreadPoolExecutor(max_workers=firecrawl_workers) as executor:
                futures = {
                    executor.submit(_fetch_one, i, item): i
                    for i, item in enumerate(batch_urls, start=1)
                }
                for future in as_completed(futures):
                    if self._stop_event.is_set():
                        break
                    fetch_results.append(future.result())

            if self._stop_event.is_set():
                self.state = "stopped"
                self._log("⏹️ Arrêté par l'utilisateur")
                return

            # Conserver l'ordre initial pour la structuration LLM (plus lisible/traceable)
            fetch_results.sort(key=lambda r: int(r.get("idx_in_batch", 0)))

            # Étape 2: Structure (séquentiel pour limiter les 429 OpenAI)
            for r in fetch_results:
                if self._stop_event.is_set():
                    break
                global_idx = int(r.get("global_idx", 0))
                idx_in_batch = int(r.get("idx_in_batch", 0))
                self.current_index = global_idx
                source_label = str(r.get("source_label", "Unknown"))
                url = str(r.get("url", ""))

                self._log(
                    f"  📄 [{global_idx}/{self.total}] (Batch {batch_num + 1} - {idx_in_batch}/{batch_size}) {source_label}"
                )

                if not r.get("ok"):
                    self.errors.append(f"[{global_idx}] Firecrawl error: {str(r.get('error', ''))[:120]}")
                    self.skipped += 1
                    continue

                raw_text = str(r.get("raw_text", "") or "")
                if not raw_text.strip():
                    self.errors.append(f"[{global_idx}] Firecrawl vide: {url[:60]}")
                    self.skipped += 1
                    continue

                try:
                    self._log(f"    📋 [{global_idx}/{self.total}] Structure…")
                    structured = self._run_text_prompt(PROMPT_STRUCTURE, raw_text, temperature=0.2)
                    if not structured.strip():
                        self.errors.append(f"[{global_idx}] Structure vide: {url[:60]}")
                        self.skipped += 1
                        continue

                    batch_buffer += structured + "\n\n"
                    batch_processed += 1
                    self.processed += 1
                    self._log(f"    ✅ [{global_idx}/{self.total}] OK - Ajouté au buffer batch")
                except Exception as exc:
                    self.errors.append(f"[{global_idx}] Erreur structure: {str(exc)[:120]}")
                    self.skipped += 1
                    self._log(f"    ❌ [{global_idx}/{self.total}] Erreur structure: {str(exc)[:60]}")
            
            # Finalisation du batch
            if self._stop_event.is_set():
                self.state = "stopped"
                self._log("⏹️ Arrêté par l'utilisateur")
                return
            
            if batch_processed == 0:
                self._log(f"⚠️ Batch {batch_num + 1}/{total_batches} - Aucun article traité")
                continue
            
            # JSON du batch
            self._log(f"🔄 Batch {batch_num + 1}/{total_batches} - Génération JSON ({batch_processed} articles)...")
            self.buffer_text = batch_buffer  # Utiliser le buffer du batch
            json_result = self.finalize_buffer()
            if json_result.get("status") != "success":
                self.errors.append(f"Batch {batch_num + 1} - Erreur JSON: {json_result.get('message')}")
                self._log(f"❌ Batch {batch_num + 1} - Erreur JSON")
                continue
            
            # DB du batch
            if not self._config or not self._config.dry_run:
                self._log(f"💾 Batch {batch_num + 1}/{total_batches} - Envoi en DB...")
                db_result = self.send_to_db()
                if db_result.get("status") == "success":
                    inserted = db_result.get("inserted", 0)
                    total_inserted += inserted
                    self._log(f"✅ Batch {batch_num + 1}/{total_batches} - {inserted} items insérés en DB")
                else:
                    self.errors.append(f"Batch {batch_num + 1} - Erreur DB: {db_result.get('message')}")
                    self._log(f"❌ Batch {batch_num + 1} - Erreur DB")
            else:
                self._log(f"✅ Batch {batch_num + 1}/{total_batches} - OK (DRY RUN)")
            
            # Reset buffer pour le prochain batch
            self.buffer_text = ""
            self.json_items = []
            self.json_preview_text = ""
        
        # Finalisation globale
        if self.processed == 0:
            self.state = "failed"
            self._log("❌ Aucun article traité avec succès")
        else:
            self.state = "completed"
            self._log(f"✅ Mega Job terminé ! {self.processed} articles traités, {total_inserted} items insérés en DB")
            if self.skipped > 0:
                self._log(f"⚠️ {self.skipped} articles ignorés (erreurs)")

    def _deduplicate_blocks(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._run_text_prompt(PROMPT_DEDUPLICATE, text, temperature=0.1).strip()

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

    def finalize_buffer(self) -> Dict[str, object]:
        if not self.buffer_text.strip():
            return {"status": "error", "message": "Buffer vide"}
        json_result = self._jsonfy(self.buffer_text)
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
            source_name=self._config.source_name if self._config else "Mega Job",
            source_link=self._config.source_link if self._config else "",
            source_date=None,
            source_raw=None,
        )
        result = insert_raw_news(enriched)
        return result


_MEGA_JOB_INSTANCE: Optional[MegaJob] = None


def get_mega_job() -> MegaJob:
    global _MEGA_JOB_INSTANCE
    if _MEGA_JOB_INSTANCE is None:
        _MEGA_JOB_INSTANCE = MegaJob()
    return _MEGA_JOB_INSTANCE
