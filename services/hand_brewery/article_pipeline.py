import json
import streamlit as st
from openai import OpenAI

from prompts.hand_brewery.structure import PROMPT_STRUCTURE
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


def run_extract_news(raw_text: str) -> dict:
    """
    Reformule (anti-plagiat) + Structure en sujets distincts.
    Remplace l'ancien run_rewrite() + run_extract_news().
    """
    if not raw_text or not raw_text.strip():
        return {
            "status": "error",
            "message": "Empty text input",
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_STRUCTURE},
                {"role": "user", "content": raw_text},
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
