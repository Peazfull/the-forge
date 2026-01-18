PROMPT_JSONFY = """
Convertis le texte en JSON STRICT au format suivant :
{
  "items": [
    { "title": "...", "content": "..." }
  ]
}

Contraintes :
- JSON valide uniquement.
- Liste vide si rien d'exploitable.
- "title" court et précis, "content" factuel.
"""
