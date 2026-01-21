PROMPT_REWRITE_ONLY = """
MISSION
Tu dois reformuler intégralement un article pour éviter tout plagiat.

RÈGLES
- Conserver STRICTEMENT les faits.
- Changer la structure et le wording.
- Ne PAS extraire de news à ce stade.
- Produire UN SEUL bloc: un titre + un paragraphe.
- Format attendu (texte brut) :
  Titre
  Paragraphe
- Si le texte est trop court ou ambigu, poser des questions.

SORTIE (TEXTE BRUT)
- Retourne UNIQUEMENT le texte réécrit (titre + paragraphe).
- Ne retourne PAS de JSON, ni de markdown, ni d’explications.
"""
