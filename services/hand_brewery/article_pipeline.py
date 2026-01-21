import json
import streamlit as st
from openai import OpenAI

from prompts.hand_brewery.rewrite_only import PROMPT_REWRITE_ONLY
from prompts.hand_brewery.split_structured import PROMPT_SPLIT_STRUCTURED
from prompts.hand_brewery.final_items import PROMPT_FINAL_ITEMS
from prompts.hand_brewery.jsonfy import PROMPT_JSONFY
from prompts.hand_brewery.json_secure import PROMPT_JSON_SECURE


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def _safe_json_load(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Invalid JSON response: {exc}",
        }


def run_rewrite(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {
            "status": "error",
            "message": "Empty text input",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_REWRITE_ONLY},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        payload = _safe_json_load(response.choices[0].message.content)
        if payload.get("status") == "error":
            return payload
        return {
            "status": "success",
            "rewrite_text": payload.get("rewrite_text", ""),
            "needs_clarification": payload.get("needs_clarification", False),
            "questions": payload.get("questions", []),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def run_split(rewrite_text: str) -> dict:
    if not rewrite_text or not rewrite_text.strip():
        return {
            "status": "error",
            "message": "Empty rewrite text",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_SPLIT_STRUCTURED},
                {"role": "user", "content": rewrite_text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        payload = _safe_json_load(response.choices[0].message.content)
        if payload.get("status") == "error":
            return payload
        return {
            "status": "success",
            "structured_news": payload.get("structured_news", []),
            "needs_clarification": payload.get("needs_clarification", False),
            "questions": payload.get("questions", []),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def run_final_items(structured_news: list) -> dict:
    if not structured_news:
        return {
            "status": "error",
            "message": "No structured news",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_FINAL_ITEMS},
                {"role": "user", "content": json.dumps({"structured_news": structured_news}, ensure_ascii=False)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        payload = _safe_json_load(response.choices[0].message.content)
        if payload.get("status") == "error":
            return payload
        return {
            "status": "success",
            "final_items": payload.get("final_items", []),
            "needs_clarification": payload.get("needs_clarification", False),
            "questions": payload.get("questions", []),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def run_jsonify(text_buffer: str) -> dict:
    if not text_buffer or not text_buffer.strip():
        return {
            "status": "error",
            "message": "Empty text buffer",
        }

    try:
        response_jsonfy = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSONFY},
                {"role": "user", "content": text_buffer},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        response_secure = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSON_SECURE},
                {"role": "user", "content": response_jsonfy.choices[0].message.content},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        payload = _safe_json_load(response_secure.choices[0].message.content)
        if payload.get("status") == "error":
            return payload
        raw_items = payload.get("items", [])
        clean_items = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            clean_items.append({
                "title": item.get("title"),
                "content": item.get("content"),
            })
        return {
            "status": "success",
            "items": clean_items,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
