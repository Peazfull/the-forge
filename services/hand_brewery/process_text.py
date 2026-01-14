def process_text(text: str) -> dict:
    """
    Étape 1 du Hand Brewery (TEXTE)

    - Reçoit du texte brut
    - (plus tard) enverra le texte à l'IA
    - Retourne un JSON structuré (mock pour l’instant)
    """

    if not text or not text.strip():
        return {
            "status": "error",
            "message": "Empty text input",
            "items": []
        }

    # MOCK TEMPORAIRE — remplacé plus tard par l’IA
    return {
        "status": "success",
        "items": [
            {
                "title": "Mock title from text",
                "content": text[:300],
                "tags": ["mock"],
                "labels": ["test"],
                "zone": ["unknown"],
                "country": [],
                "score": 5.0
            }
        ]
    }
