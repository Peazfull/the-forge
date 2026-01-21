PROMPT_REWRITE_ONLY = """
MISSION
Tu dois reformuler intégralement un article pour éviter tout plagiat,
sans perdre d'informations importantes.

RÈGLES
- Conserver STRICTEMENT tous les faits, chiffres, dates, noms propres et détails.
- Ne rien résumer : réécrire l’article COMPLET, pas un résumé.
- Conserver la structure et l’ordre des informations du texte source.
- Longueur cible : ~95-115% de la longueur utile (mêmes infos).
- Changer le wording et la formulation pour éviter le plagiat.
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
