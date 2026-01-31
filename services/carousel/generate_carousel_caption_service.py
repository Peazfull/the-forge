from typing import Dict, List
import re
import streamlit as st
from openai import OpenAI

from prompts.carousel.generate_carousel_caption import PROMPT_GENERATE_CAROUSEL_CAPTION
from db.supabase_client import get_supabase

REQUEST_TIMEOUT = 30

CTA_LINE = "Rejoignez la liste d'attente pour notre future newsletter 100% gratuite (lien en bio)."
CAPTION_BUCKET = "carousel-eco-slides"
CAPTION_FILE = "caption.txt"


def generate_caption_from_items(items: List[Dict[str, object]]) -> Dict[str, object]:
    """
    Génère une caption Instagram à partir d'une liste d'items carousel.
    """
    if not items:
        return {"status": "error", "message": "Aucun item disponible"}
    
    lines = []
    for item in items:
        title = item.get("title") or ""
        content = item.get("content") or ""
        lines.append(f"- {title}\n  {content[:240]}")
    
    user_input = "ACTUS DU JOUR:\n" + "\n\n".join(lines)
    
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT_GENERATE_CAROUSEL_CAPTION},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT
        )
        caption = (response.choices[0].message.content or "").strip()
        
        caption = sanitize_caption(caption)
        
        return {"status": "success", "caption": caption}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def sanitize_caption(text: str) -> str:
    """Supprime le markdown (gras, italique, code) pour Instagram."""
    if not text:
        return ""
    cleaned = re.sub(r"`{1,3}([^`]+)`{1,3}", r"\1", text)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)
    return cleaned.strip()


def upload_caption_text(text: str) -> bool:
    """Upload la caption dans le bucket storage (upsert)."""
    try:
        supabase = get_supabase()
        supabase.storage.from_(CAPTION_BUCKET).upload(
            CAPTION_FILE,
            text.encode("utf-8"),
            file_options={"content-type": "text/plain; charset=utf-8", "upsert": True}
        )
        return True
    except Exception:
        return False


def read_caption_text() -> str:
    """Récupère la caption depuis le bucket storage."""
    try:
        supabase = get_supabase()
        data = supabase.storage.from_(CAPTION_BUCKET).download(CAPTION_FILE)
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""
