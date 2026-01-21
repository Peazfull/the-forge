import json
import streamlit as st
from openai import OpenAI

from prompts.hand_brewery.rewrite_only import PROMPT_REWRITE_ONLY
from prompts.hand_brewery.extract_news import PROMPT_EXTRACT_NEWS
from prompts.hand_brewery.jsonfy import PROMPT_JSONFY


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
        )
        rewrite_text = (response.choices[0].message.content or "").strip()
        if not rewrite_text:
            return {
                "status": "error",
                "message": "Empty rewrite output",
            }
        return {
            "status": "success",
            "rewrite_text": rewrite_text,
            "needs_clarification": False,
            "questions": [],
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


def run_extract_news(rewrite_text: str) -> dict:
    if not rewrite_text or not rewrite_text.strip():
        return {
            "status": "error",
            "message": "Empty rewrite text",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_EXTRACT_NEWS},
                {"role": "user", "content": rewrite_text},
            ],
            temperature=0.2,
        )
        extracted_text = (response.choices[0].message.content or "").strip()
        if not extracted_text:
            return {
                "status": "error",
                "message": "Empty extract output",
            }
        return {
            "status": "success",
            "extracted_text": extracted_text,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def run_jsonify(extract_text: str) -> dict:
    if not extract_text or not extract_text.strip():
        return {
            "status": "error",
            "message": "Empty extract text",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSONFY},
                {"role": "user", "content": extract_text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        payload = _safe_json_load(response.choices[0].message.content)
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
