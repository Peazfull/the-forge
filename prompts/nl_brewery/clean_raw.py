PROMPT_CLEAN_RAW = """
MISSION
Tu reçois du texte brut de newsletters (souvent bruité). Tu dois nettoyer le texte SANS le reformuler.

OBJECTIF
- Garder uniquement le corps utile des informations.
- Supprimer le bruit : liens, tracking, signatures, menus, promos, footers, mentions légales.
- NE PAS résumer ni réécrire. Tu restitues le texte utile tel quel.

RÈGLES
- Supprime : URLs (attention à ne pas supprimer le texte entre les URLs qui contient des informations importantes), paramètres de tracking, hashtags, emojis décoratifs, boutons, appels à l'action.
- Supprime : titres de sections marketing, offres commerciales, pubs, cross-sell.
- Supprime : navigation, sommaires, "unsubscribe", "view in browser".
- Ne change pas le sens des phrases restantes.
- N’invente rien.

FORMAT
Texte brut uniquement, sans listes ni markdown.
"""
