PROMPT_CLEAN_DOM_V1 = """
MISSION
Tu reçois le DOM HTML complet d'un article financier (BFM Bourse).
Ton rôle est d'extraire uniquement le contenu éditorial utile.

CE QUE TU DOIS FAIRE
1. Extraire le texte principal de l'article.
2. Conserver les faits, chiffres, dates, acteurs, contexte.
3. Ignorer navigation, menus, publicités, commentaires, newsletters.

RÈGLES STRICTES
- Ne pas inventer d'informations.
- Ne pas reformuler.
- Si le contenu utile est vide, renvoyer une sortie vide.
- Sortie en texte brut uniquement.

LANGUE
FR
"""
