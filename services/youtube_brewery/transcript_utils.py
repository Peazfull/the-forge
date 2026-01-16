import json
from typing import Dict, List, Optional, Tuple

import requests
from yt_dlp import YoutubeDL


LANG_PREFERENCES = ["fr", "fr-FR", "fr-CA", "en", "en-US", "en-GB"]
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
    subtitles = info.get("subtitles") or {}
    auto_captions = info.get("automatic_captions") or {}

    for lang in LANG_PREFERENCES:
        entry = _select_caption_entry(subtitles.get(lang, []))
        if entry:
            return entry
        entry = _select_caption_entry(auto_captions.get(lang, []))
        if entry:
            return entry

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


def fetch_video_transcript(video_url: str) -> str:
    """
    Récupère le transcript d'une vidéo YouTube via yt-dlp.
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
