PROMPT_CLEAN_DOM_V2 = """
MISSION
Tu reçois le DOM HTML complet d'un article financier (BFM Bourse).
Tu dois extraire le contenu éditorial même si le HTML est bruité.

CE QUE TU DOIS FAIRE
1. Repérer les paragraphes d'article.
2. Conserver les faits, chiffres, dates, acteurs, contexte.
3. Ignorer tout le reste (menus, pubs, widgets).

RÈGLES STRICTES
- Ne pas inventer d'informations.
- Ne pas reformuler.
- Sortie en texte brut uniquement.

LANGUE
FR
"""
