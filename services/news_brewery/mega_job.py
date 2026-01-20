import json
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
from openai import OpenAI

from services.raw_storage.raw_news_service import enrich_raw_items, insert_raw_news
from prompts.news_brewery.deduplicate import PROMPT_DEDUPLICATE
from prompts.news_brewery.jsonfy import PROMPT_JSONFY
from prompts.news_brewery.json_secure import PROMPT_JSON_SECURE


REQUEST_TIMEOUT = 60
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


@dataclass
class MegaJobConfig:
    source_name: str
    source_link: str
    remove_buffer_after_success: bool
    dry_run: bool


class MegaJob:
    def __init__(self) -> None:
        self.buffer_text: str = ""
        self.json_preview_text: str = ""
        self.json_items: List[Dict[str, object]] = []
        self._config: Optional[MegaJobConfig] = None

    def set_config(self, config: MegaJobConfig) -> None:
        self._config = config

    def set_buffer_text(self, text: str) -> None:
        self.buffer_text = text or ""

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
        deduped = self._deduplicate_blocks(self.buffer_text)
        json_result = self._jsonfy(deduped)
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
