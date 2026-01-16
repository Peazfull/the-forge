from typing import Optional
from yt_dlp import YoutubeDL


def _resolve_channel_id_from_handle(handle: str) -> Optional[str]:
    """
    Résout un @handle YouTube en channel_id via yt-dlp.
    """
    url = f"https://www.youtube.com/@{handle}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "noplaylist": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if isinstance(info, dict):
            return info.get("channel_id") or info.get("channel")
    except Exception:
        return None
    return None


def get_rss_url_from_channel_url(channel_url: str) -> Optional[str]:
    """
    Transforme une URL de chaîne YouTube en URL RSS exploitable.

    Supporte :
    - https://www.youtube.com/@handle
    - https://www.youtube.com/channel/UCxxxx

    Retourne :
    - URL RSS si reconnue
    - None si format non supporté
    """

    # Cas 1 : URL avec @handle
    # Exemple : https://www.youtube.com/@BNPParibasProduitsdeBourse
    if "/@" in channel_url:
        handle = channel_url.split("/@")[-1].strip("/")
        channel_id = _resolve_channel_id_from_handle(handle)
        if channel_id:
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        return None

    # Cas 2 : URL avec channel ID
    # Exemple : https://www.youtube.com/channel/UCxxxx
    if "/channel/" in channel_url:
        channel_id = channel_url.split("/channel/")[-1].strip("/")
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    # Sinon : format inconnu
    return None
