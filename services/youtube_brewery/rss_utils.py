from typing import Optional


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
        return f"https://www.youtube.com/feeds/videos.xml?user={handle}"

    # Cas 2 : URL avec channel ID
    # Exemple : https://www.youtube.com/channel/UCxxxx
    if "/channel/" in channel_url:
        channel_id = channel_url.split("/channel/")[-1].strip("/")
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    # Sinon : format inconnu
    return None
