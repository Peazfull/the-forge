import json
import time
from typing import Dict, List, Optional, Tuple

import requests
from yt_dlp import YoutubeDL


LANG_PREFERENCES = ["en", "en-US", "en-GB", "fr", "fr-FR", "fr-CA"]
EXT_PREFERENCES = ["vtt", "json3", "srv3", "ttml"]


def _select_caption_entry(entries: List[Dict]) -> Optional[Dict]:
    if not entries:
        return None

    for ext in EXT_PREFERENCES:
        for entry in entries:
            if entry.get("ext") == ext and entry.get("url"):
                return entry

    for entry in entries:
        if entry.get("url"):
            return entry

    return None


def _find_caption(info: Dict) -> Optional[Dict]:
    """
    Cherche un transcript disponible. Priorité: anglais (langue la plus commune),
    puis français, puis n'importe quelle langue disponible.
    """
    subtitles = info.get("subtitles") or {}
    auto_captions = info.get("automatic_captions") or {}

    # 1. Chercher dans les langues préférées (anglais en priorité)
    for lang in LANG_PREFERENCES:
        entry = _select_caption_entry(subtitles.get(lang, []))
        if entry:
            return entry
        entry = _select_caption_entry(auto_captions.get(lang, []))
        if entry:
            return entry

    # 2. Si rien trouvé, prendre n'importe quelle langue disponible
    for source in (subtitles, auto_captions):
        for entries in source.values():
            entry = _select_caption_entry(entries)
            if entry:
                return entry

    return None


def _parse_vtt(text: str) -> str:
    lines = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("WEBVTT"):
            continue
        if "-->" in clean:
            continue
        if clean.isdigit():
            continue
        lines.append(clean)
    return " ".join(lines).strip()


def _parse_json3(payload: str) -> str:
    try:
        data = json.loads(payload)
    except Exception:
        return ""

    texts = []
    for event in data.get("events", []):
        segs = event.get("segs") or []
        for seg in segs:
            txt = seg.get("utf8")
            if txt:
                texts.append(txt.replace("\n", " ").strip())
    return " ".join(texts).strip()


def fetch_video_transcript(video_url: str, max_retries: int = 3) -> str:
    """
    Récupère le transcript d'une vidéo YouTube via yt-dlp avec retry automatique.
    
    Args:
        video_url: URL de la vidéo YouTube
        max_retries: Nombre maximum de tentatives (défaut: 3)
    
    Returns:
        Le transcript en texte brut
        
    Raises:
        RuntimeError: Si toutes les tentatives échouent
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return _fetch_video_transcript_single(video_url)
        except Exception as e:
            last_error = e
            error_str = str(e)
            
            # Si rate limit (429) et pas la dernière tentative, on réessaye
            if "429" in error_str and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                time.sleep(wait_time)
                continue
            
            # Si autre erreur et pas la dernière tentative, on attend moins longtemps
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            
            # Dernière tentative échouée, on raise
            raise
    
    raise RuntimeError(f"Échec après {max_retries} tentatives: {last_error}")


def _fetch_video_transcript_single(video_url: str) -> str:
    """
    Tente de récupérer le transcript une seule fois (sans retry).
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": True,
        "socket_timeout": 15,
        "retries": 1,
        "extractor_retries": 1,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception as e:
        raise RuntimeError(f"Impossible d'extraire les infos vidéo: {e}")

    if not isinstance(info, dict):
        raise RuntimeError("Format de réponse yt-dlp invalide")

    caption = _find_caption(info)
    if not caption:
        raise RuntimeError("Aucun transcript disponible (sous-titres introuvables)")

    url = caption.get("url")
    ext = caption.get("ext") or ""
    if not url:
        raise RuntimeError("URL de transcript introuvable")

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Erreur téléchargement transcript: {e}")

    raw = r.text or ""

    if ext == "json3":
        transcript = _parse_json3(raw)
    else:
        transcript = _parse_vtt(raw)

    if not transcript or len(transcript) < 100:
        raise RuntimeError("Transcript vide ou trop court")

    return transcript
