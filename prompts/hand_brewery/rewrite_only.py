PROMPT_REWRITE_ONLY = """
MISSION
Tu dois reformuler intégralement un article pour éviter tout plagiat,
sans perdre d'informations importantes.

RÈGLES
- Conserver STRICTEMENT tous les faits et détails.
- Ne rien résumer : la sortie doit être aussi complète que l’original.
- Longueur cible : ~90-110% de la longueur de l’article utile (mêmes infos).
- Changer la structure et le wording pour éviter le plagiat.
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
