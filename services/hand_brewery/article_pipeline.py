import json
import streamlit as st
from openai import OpenAI

from prompts.hand_brewery.rewrite_only import PROMPT_REWRITE_ONLY
from prompts.hand_brewery.split_structured import PROMPT_SPLIT_STRUCTURED
from prompts.hand_brewery.final_items import PROMPT_FINAL_ITEMS
from prompts.hand_brewery.extract_news import PROMPT_EXTRACT_NEWS


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


def run_jsonify(structured_news: list) -> dict:
    if not structured_news:
        return {
            "status": "error",
            "message": "No structured news",
        }

    items = []
    for idx, news in enumerate(structured_news, start=1):
        sections = news.get("sections", []) if isinstance(news, dict) else []
        if not sections:
            continue
        first = sections[0] if isinstance(sections[0], dict) else {}
        title = first.get("title") or f"News {idx}"
        contents = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            content = section.get("content")
            if content:
                contents.append(content)
        content_text = "\n\n".join(contents).strip()
        items.append({
            "title": title,
            "content": content_text,
        })

    return {
        "status": "success",
        "items": items,
    }
