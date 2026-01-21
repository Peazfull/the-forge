import json
import streamlit as st
from openai import OpenAI

from prompts.hand_brewery.rewrite_text import PROMPT_REWRITE_TEXT
from prompts.hand_brewery.extract_news import PROMPT_EXTRACT_NEWS
from prompts.hand_brewery.final_items import PROMPT_FINAL_ITEMS


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def _safe_json_loads(raw: str, fallback: dict) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return fallback


def rewrite_article(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {
            "status": "error",
            "message": "Empty text input",
            "rewrite_text": "",
            "needs_clarification": True,
            "questions": ["Le texte est vide. Peux-tu coller un article complet ?"],
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_REWRITE_TEXT},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        data = _safe_json_loads(response.choices[0].message.content, {})
        return {
            "status": "success",
            "rewrite_text": data.get("rewrite_text", "").strip(),
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "questions": data.get("questions", []) or [],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "rewrite_text": "",
            "needs_clarification": False,
            "questions": [],
        }


def extract_structured_news(rewrite_text: str) -> dict:
    if not rewrite_text or not rewrite_text.strip():
        return {
            "status": "error",
            "message": "Empty rewrite_text input",
            "structured_news": [],
            "needs_clarification": True,
            "questions": ["Le texte reformulé est vide. Veux-tu relancer l'étape 1 ?"],
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_EXTRACT_NEWS},
                {"role": "user", "content": rewrite_text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = _safe_json_loads(response.choices[0].message.content, {})
        return {
            "status": "success",
            "structured_news": data.get("structured_news", []) or [],
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "questions": data.get("questions", []) or [],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "structured_news": [],
            "needs_clarification": False,
            "questions": [],
        }


def build_final_items(structured_news: list) -> dict:
    if not structured_news:
        return {
            "status": "error",
            "message": "No structured news provided",
            "final_items": [],
            "needs_clarification": True,
            "questions": ["Aucune news structurée. Veux-tu relancer l'étape 2 ?"],
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_FINAL_ITEMS},
                {"role": "user", "content": json.dumps({"structured_news": structured_news}, ensure_ascii=False)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = _safe_json_loads(response.choices[0].message.content, {})
        return {
            "status": "success",
            "final_items": data.get("final_items", []) or [],
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "questions": data.get("questions", []) or [],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "final_items": [],
            "needs_clarification": False,
            "questions": [],
        }
