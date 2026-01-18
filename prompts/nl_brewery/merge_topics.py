PROMPT_MERGE_TOPICS = """
MISSION
Tu reçois un texte nettoyé de newsletters. Tu dois regrouper les informations qui parlent du MÊME sujet.

OBJECTIF
- Regrouper les passages similaires pour éviter les doublons.
- Produire un grand paragraphe détaillé par sujet.
- Reformuler, mais sans perdre d’informations.

RÈGLES
- 1 sujet = 1 paragraphe.
- Si deux passages parlent du même sujet, tu fusionnes en un seul paragraphe complet.
- Conserve tous les détails utiles (acteurs, chiffres, dates, contexte, causes, conséquences).
- Ton neutre et factuel.
- N’invente rien, ne comble pas les manques.

FORMAT
Texte brut uniquement, avec un paragraphe par sujet (séparés par une ligne vide).
"""
