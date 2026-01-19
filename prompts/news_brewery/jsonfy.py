PROMPT_JSONFY = """
MISSION
Convertir un texte structuré en JSON strict.

FORMAT JSON ATTENDU
{"items":[{"title":"...","content":"..."}]}

RÈGLES
- Ne pas inventer ni reformuler.
- Chaque bloc "Titre + Paragraphe" devient un item.
- Aucun texte hors JSON.
"""
