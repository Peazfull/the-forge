from typing import Dict
import re
import streamlit as st
from openai import OpenAI

from prompts.breaking.generate_breaking_caption import PROMPT_GENERATE_BREAKING_CAPTION
from prompts.breaking.generate_breaking_linkedin import PROMPT_GENERATE_BREAKING_LINKEDIN
from db.supabase_client import get_supabase

REQUEST_TIMEOUT = 30

CAPTION_BUCKET = "carousel-breaking-slides"
CAPTION_FILE = "caption.txt"
LINKEDIN_FILE = "linkedin.txt"


def generate_caption_from_breaking(title: str, content: str) -> Dict[str, object]:
    if not title or not content:
        return {"status": "error", "message": "Titre ou contenu manquant"}

    user_input = f"TITRE: {title}\n\nCONTENU: {content}"
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_GENERATE_BREAKING_CAPTION},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT,
        )
        caption = (response.choices[0].message.content or "").strip()
        caption = _sanitize_caption(caption)
        return {"status": "success", "caption": caption}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_linkedin_from_breaking(title: str, content: str) -> Dict[str, object]:
    if not title or not content:
        return {"status": "error", "message": "Titre ou contenu manquant"}

    user_input = f"BREAKING:\nTITRE: {title}\n\nCONTENU: {content}"
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_GENERATE_BREAKING_LINKEDIN},
                {"role": "user", "content": user_input},
            ],
            temperature=0.6,
            timeout=REQUEST_TIMEOUT,
        )
        text = (response.choices[0].message.content or "").strip()
        text = _strip_emojis(_strip_markdown(text))
        return {"status": "success", "text": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def upload_caption_text(text: str) -> Dict[str, object]:
    try:
        supabase = get_supabase()
        supabase.storage.from_(CAPTION_BUCKET).upload(
            CAPTION_FILE,
            text.encode("utf-8"),
            file_options={"content-type": "text/plain; charset=utf-8", "upsert": "true"},
        )
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def read_caption_text() -> str:
    try:
        supabase = get_supabase()
        data = supabase.storage.from_(CAPTION_BUCKET).download(CAPTION_FILE)
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""


def upload_linkedin_text(text: str) -> bool:
    try:
        supabase = get_supabase()
        supabase.storage.from_(CAPTION_BUCKET).upload(
            LINKEDIN_FILE,
            text.encode("utf-8"),
            file_options={"content-type": "text/plain; charset=utf-8", "upsert": "true"},
        )
        return True
    except Exception:
        return False


def read_linkedin_text() -> str:
    try:
        supabase = get_supabase()
        data = supabase.storage.from_(CAPTION_BUCKET).download(LINKEDIN_FILE)
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""


def _sanitize_caption(text: str) -> str:
    cleaned = _strip_markdown(text)
    cleaned = _keep_single_leading_emoji_per_line(cleaned)
    return cleaned.strip()


def _strip_markdown(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"`{1,3}([^`]+)`{1,3}", r"\1", text)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)
    return cleaned


def _keep_single_leading_emoji_per_line(text: str) -> str:
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")

    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        leading_emoji = ""
        if stripped and emoji_re.match(stripped[0]):
            leading_emoji = stripped[0]
            stripped = stripped[1:].lstrip()

        stripped = emoji_re.sub("", stripped).strip()
        if leading_emoji:
            lines.append(f"{leading_emoji} {stripped}".rstrip())
        else:
            lines.append(stripped)

    return "\n".join(lines)


def _strip_emojis(text: str) -> str:
    if not text:
        return ""
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    return emoji_re.sub("", text).strip()
