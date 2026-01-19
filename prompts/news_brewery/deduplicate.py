PROMPT_DEDUPLICATE = """
MISSION
Tu reçois une liste de sujets structurés (Titre + Paragraphe).
Tu dois dédoublonner globalement les sujets similaires.

CE QUE TU DOIS FAIRE
1. Supprimer les doublons ou sujets quasi identiques.
2. Conserver la version la plus complète.
3. Ne pas reformuler ni modifier le contenu.

RÈGLES STRICTES
- Ne pas inventer d'informations.
- Sortie en texte brut uniquement, sans JSON, sans markdown.

FORMAT DE SORTIE
Titre 1
Paragraphe détaillé du titre 1.

Titre 2
Paragraphe détaillé du titre 2.
"""
