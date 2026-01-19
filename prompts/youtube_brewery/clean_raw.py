PROMPT_CLEAN_RAW = """
MISSION
Tu reçois un transcript brut de vidéo YouTube. Tu dois nettoyer le texte.

CE QUE TU DOIS FAIRE
1. Supprimer les URLs, mentions d'abonnement, appels à l'action, promos.
2. Retirer les répétitions inutiles, tics de langage et bruit.
3. Conserver uniquement le contenu informationnel utile.

RÈGLES STRICTES
- Ne pas inventer d'informations.
- Ne pas reformuler, juste nettoyer.
- Si rien d'exploitable, renvoyer une sortie vide.

FORMAT DE SORTIE
Texte brut nettoyé, sans JSON, sans markdown, sans listes.
"""
