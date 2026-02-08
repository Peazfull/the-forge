from typing import Dict, List
import re
import time
import streamlit as st
from openai import OpenAI

from prompts.carousel.bourse.generate_carousel_caption import PROMPT_GENERATE_CAROUSEL_CAPTION
from prompts.carousel.bourse.generate_carousel_linkedin import PROMPT_GENERATE_LINKEDIN_POST
from db.supabase_client import get_supabase

REQUEST_TIMEOUT = 30
MAX_UPLOAD_RETRIES = 3
MAX_API_RETRIES = 3  # Retry pour les appels API OpenAI
RETRY_DELAY_SECONDS = 2
API_RETRY_DELAY = 10  # Délai pour le rate limiting

CTA_LINE = "Rejoignez la liste d'attente pour notre future newsletter 100% gratuite (lien en bio)."
CAPTION_BUCKET = "carousel-bourse-slides"
CAPTION_FILE = "caption.txt"
LINKEDIN_FILE = "linkedin.txt"


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
        
        # Retry logic avec délai progressif pour gérer le rate limiting
        for attempt in range(MAX_API_RETRIES):
            try:
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
                break
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg and attempt < MAX_API_RETRIES - 1:
                    delay = API_RETRY_DELAY * (attempt + 1)
                    time.sleep(delay)
                    continue
                elif attempt < MAX_API_RETRIES - 1:
                    time.sleep(2)
                    continue
                else:
                    raise e
        
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
    cleaned = _keep_single_leading_emoji_per_line(cleaned)
    return cleaned.strip()


def _keep_single_leading_emoji_per_line(text: str) -> str:
    """
    Conserve un seul emoji au début de chaque ligne (si présent),
    supprime tous les emojis ailleurs dans la ligne.
    """
    # Plage d'emojis courants + symboles
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        # Capturer le premier emoji au début (s'il existe)
        leading_emoji = ""
        if stripped and emoji_re.match(stripped[0]):
            leading_emoji = stripped[0]
            stripped = stripped[1:].lstrip()
        
        # Retirer tous les emojis restants dans la ligne
        stripped = emoji_re.sub("", stripped).strip()
        
        if leading_emoji:
            lines.append(f"{leading_emoji} {stripped}".rstrip())
        else:
            lines.append(stripped)
    
    return "\n".join(lines)


def upload_caption_text(text: str) -> Dict[str, object]:
    """Upload la caption dans le bucket storage (upsert) avec retry logic."""
    last_error = None
    
    for attempt in range(1, MAX_UPLOAD_RETRIES + 1):
        try:
            supabase = get_supabase()
            supabase.storage.from_(CAPTION_BUCKET).upload(
                CAPTION_FILE,
                text.encode("utf-8"),
                file_options={"content-type": "text/plain; charset=utf-8", "upsert": "true"}
            )
            return {"status": "success"}
        except Exception as e:
            last_error = str(e)
            # Si c'est une erreur 500/502 (timeout Cloudflare), on réessaye
            if attempt < MAX_UPLOAD_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
    
    # Si toutes les tentatives échouent
    return {"status": "error", "message": f"Upload échec après {MAX_UPLOAD_RETRIES} tentatives: {last_error}"}


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


def generate_linkedin_from_items(items: List[Dict[str, object]]) -> Dict[str, object]:
    """
    Génère un post LinkedIn à partir d'une liste d'items carousel.
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
                {"role": "system", "content": PROMPT_GENERATE_LINKEDIN_POST},
                {"role": "user", "content": user_input}
            ],
            temperature=0.6,
            timeout=REQUEST_TIMEOUT
        )
        text = (response.choices[0].message.content or "").strip()
        text = sanitize_caption(text)
        return {"status": "success", "text": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def upload_linkedin_text(text: str) -> bool:
    """Upload le post LinkedIn dans le bucket storage (upsert)."""
    try:
        supabase = get_supabase()
        supabase.storage.from_(CAPTION_BUCKET).upload(
            LINKEDIN_FILE,
            text.encode("utf-8"),
            file_options={"content-type": "text/plain; charset=utf-8", "upsert": "true"}
        )
        return True
    except Exception:
        return False


def read_linkedin_text() -> str:
    """Récupère le post LinkedIn depuis le bucket storage."""
    try:
        supabase = get_supabase()
        data = supabase.storage.from_(CAPTION_BUCKET).download(LINKEDIN_FILE)
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""
