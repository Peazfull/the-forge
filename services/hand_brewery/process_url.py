from services.hand_brewery.firecrawl_client import fetch_url_text
from services.hand_brewery.process_text import process_text


def process_url(url: str) -> dict:
    raw_text = fetch_url_text(url)
    return process_text(raw_text)
