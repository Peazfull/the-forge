import os
import streamlit as st
from firecrawl import FirecrawlApp
import time
import random
from typing import Iterable, Optional


DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SEC = 45


def _is_retryable_error(msg: str) -> bool:
    m = (msg or "").lower()
    # Firecrawl (ou proxy) peut renvoyer des codes via message/exception.
    retry_markers = [
        "429",
        "rate limit",
        "too many requests",
        "timeout",
        "timed out",
        "temporarily",
        "503",
        "502",
        "504",
        "overloaded",
        "gateway",
        "connection reset",
        "connection aborted",
        "ssl",
    ]
    non_retry_markers = [
        "402",  # credits / paiement
        "payment",
        "credit",
        "quota exceeded",
        "invalid api key",
        "unauthorized",
        "forbidden",
    ]
    if any(x in m for x in non_retry_markers):
        return False
    return any(x in m for x in retry_markers)


def _scrape_with_retries(
    *,
    url: str,
    formats: Iterable[str],
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> object:
    api_key = st.secrets.get("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY manquante dans les secrets")

    # Instancier par appel (sécurité thread). Si besoin d'optim, on pourra passer à du thread-local.
    app = FirecrawlApp(api_key=api_key)

    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            # Le SDK Firecrawl ne permet pas toujours un timeout paramétrable.
            # On garde un timeout logique via retries + délai et on compte sur le SDK pour les timeouts réseau.
            return app.scrape(url, formats=list(formats))
        except Exception as e:
            last_exc = e
            msg = str(e)
            if attempt >= max_retries or not _is_retryable_error(msg):
                raise RuntimeError(f"Firecrawl error: {msg}")

            # Backoff exponentiel avec jitter
            base = min(2 ** attempt, 16)
            jitter = random.uniform(0.2, 0.9)
            sleep_s = min(timeout_sec, base + jitter)
            time.sleep(sleep_s)

    raise RuntimeError(f"Firecrawl error: {str(last_exc) if last_exc else 'unknown'}")


def fetch_url_text(url: str) -> str:
    """
    Récupère le texte principal d'une page via Firecrawl.
    Gère les erreurs de crédits / API.
    """
    try:
        result = _scrape_with_retries(url=url, formats=["markdown"])

        # Firecrawl renvoie un Document (pas un dict)
        text = ""
        if isinstance(result, dict):
            text = result.get("markdown", "") or result.get("content", "")
        else:
            text = getattr(result, "markdown", "") or getattr(result, "content", "")
            if not text and hasattr(result, "model_dump"):
                data = result.model_dump()
                text = data.get("markdown", "") or data.get("content", "")
        text = (text or "").strip()

        if not text or len(text) < 300:
            raise RuntimeError("Contenu trop court ou vide après scraping")

        return text

    except Exception as e:
        raise RuntimeError(str(e))


def fetch_url_html(url: str) -> str:
    """
    Récupère le HTML d'une page via Firecrawl.
    Utile pour parser des listes d'URLs avec dates.
    """
    try:
        result = _scrape_with_retries(url=url, formats=["html"])
        html = ""
        if isinstance(result, dict):
            html = result.get("html", "") or result.get("content", "")
        else:
            html = getattr(result, "html", "") or getattr(result, "content", "")
            if not html and hasattr(result, "model_dump"):
                data = result.model_dump()
                html = data.get("html", "") or data.get("content", "")
        html = (html or "").strip()

        if not html or len(html) < 300:
            raise RuntimeError("HTML trop court ou vide après scraping")

        return html

    except Exception as e:
        raise RuntimeError(str(e))
