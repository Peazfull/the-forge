import os
import streamlit as st
from firecrawl import FirecrawlApp


def fetch_url_text(url: str) -> str:
    """
    Récupère le texte principal d'une page via Firecrawl.
    Gère les erreurs de crédits / API.
    """
    api_key = st.secrets.get("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_API_KEY")

    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY manquante dans les secrets")

    app = FirecrawlApp(api_key=api_key)

    try:
        result = app.scrape(
            url,
            formats=["markdown"],  # texte propre
        )

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
        # On remonte une erreur claire (crédits, site bloqué, etc.)
        raise RuntimeError(f"Firecrawl error: {str(e)}")


def fetch_url_html(url: str) -> str:
    """
    Récupère le HTML d'une page via Firecrawl.
    Utile pour parser des listes d'URLs avec dates.
    """
    api_key = st.secrets.get("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_API_KEY")

    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY manquante dans les secrets")

    app = FirecrawlApp(api_key=api_key)

    try:
        result = app.scrape(
            url,
            formats=["html"],
        )
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
        raise RuntimeError(f"Firecrawl error: {str(e)}")
