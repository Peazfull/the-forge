import json
import streamlit as st
from openai import OpenAI
from typing import Dict

from prompts.youtube_brewery.clean_raw import PROMPT_CLEAN_RAW
from prompts.youtube_brewery.merge_topics import PROMPT_MERGE_TOPICS
from prompts.youtube_brewery.journalist import PROMPT_JOURNALIST
from prompts.youtube_brewery.copywriter import PROMPT_COPYWRITER
from prompts.youtube_brewery.jsonfy import PROMPT_JSONFY
from prompts.youtube_brewery.json_secure import PROMPT_JSON_SECURE


REQUEST_TIMEOUT = 45
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def _run_text_prompt(prompt: str, content: str, temperature: float = 0.2) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        temperature=temperature,
        timeout=REQUEST_TIMEOUT
    )
    return response.choices[0].message.content or ""


def clean_raw_text(raw_text: str) -> Dict[str, object]:
    if not raw_text or not raw_text.strip():
        return {"status": "error", "message": "Transcript vide", "text": ""}
    try:
        cleaned = _run_text_prompt(PROMPT_CLEAN_RAW, raw_text, temperature=0)
        return {"status": "success", "text": cleaned.strip()}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "text": ""}


def merge_topics_text(cleaned_text: str) -> Dict[str, object]:
    if not cleaned_text or not cleaned_text.strip():
        return {"status": "error", "message": "Texte nettoyé vide", "text": ""}
    try:
        merged = _run_text_prompt(PROMPT_MERGE_TOPICS, cleaned_text, temperature=0.2)
        return {"status": "success", "text": merged.strip()}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "text": ""}


def journalist_text(merged_text: str) -> Dict[str, object]:
    if not merged_text or not merged_text.strip():
        return {"status": "error", "message": "Texte traité vide", "text": ""}
    try:
        journalist = _run_text_prompt(PROMPT_JOURNALIST, merged_text, temperature=0.2)
        return {"status": "success", "text": journalist.strip()}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "text": ""}


def copywriter_text(journalist_output: str) -> Dict[str, object]:
    if not journalist_output or not journalist_output.strip():
        return {"status": "error", "message": "Texte journalist vide", "text": ""}
    try:
        copywritten = _run_text_prompt(PROMPT_COPYWRITER, journalist_output, temperature=0.2)
        return {"status": "success", "text": copywritten.strip()}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "text": ""}


def jsonfy_text(journalist_output: str) -> Dict[str, object]:
    if not journalist_output or not journalist_output.strip():
        return {"status": "error", "message": "Texte vide", "items": []}
    try:
        response_jsonfy = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSONFY},
                {"role": "user", "content": journalist_output}
            ],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=REQUEST_TIMEOUT
        )

        raw_json = response_jsonfy.choices[0].message.content or ""

        response_secure = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_JSON_SECURE},
                {"role": "user", "content": raw_json}
            ],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=REQUEST_TIMEOUT
        )

        secure_json = response_secure.choices[0].message.content or ""
        data = json.loads(secure_json)

        return {"status": "success", "items": data.get("items", [])}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "items": []}


def process_transcript(text: str) -> dict:
    if not text or not text.strip():
        return {"status": "error", "message": "Empty transcript", "items": []}

    try:
        cleaned = clean_raw_text(text)
        if cleaned.get("status") != "success":
            return {"status": "error", "message": cleaned.get("message", "Erreur"), "items": []}

        merged = merge_topics_text(cleaned.get("text", ""))
        if merged.get("status") != "success":
            return {"status": "error", "message": merged.get("message", "Erreur"), "items": []}

        journalist = journalist_text(merged.get("text", ""))
        if journalist.get("status") != "success":
            return {"status": "error", "message": journalist.get("message", "Erreur"), "items": []}

        copywritten = copywriter_text(journalist.get("text", ""))
        if copywritten.get("status") != "success":
            return {"status": "error", "message": copywritten.get("message", "Erreur"), "items": []}

        json_result = jsonfy_text(copywritten.get("text", ""))
        if json_result.get("status") != "success":
            return {"status": "error", "message": json_result.get("message", "Erreur"), "items": []}

        return {"status": "success", "items": json_result.get("items", [])}
    except Exception as e:
        return {"status": "error", "message": str(e), "items": []}
