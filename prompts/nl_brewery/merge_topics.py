PROMPT_MERGE_TOPICS = """
MISSION
Tu reçois un texte nettoyé de newsletters. Tu dois regrouper les informations qui parlent du MÊME sujet.

OBJECTIF
- Regrouper les passages similaires pour éviter les doublons.
- Produire un paragraphe détaillé par sujet.
- Reformuler uniquement si nécessaire, sans perdre d’informations.

RÈGLES
- 1 sujet = 1 bloc.
- Si deux passages parlent du même sujet, tu fusionnes en un seul paragraphe complet.
- Conserve tous les détails utiles (acteurs, chiffres, dates, contexte, causes, conséquences).
- Ton neutre et factuel.
- N’invente rien, ne comble pas les manques.

FORMAT DE SORTIE OBLIGATOIRE
Pour chaque sujet :
Titre clair et factuel
Paragraphe détaillé associé

Les blocs sont séparés par une ligne vide.
Pas de JSON.
"""
