PROMPT_REWRITE_ONLY = """
MISSION
Tu dois reformuler intégralement un article pour éviter tout plagiat.

RÈGLES
- Conserver STRICTEMENT les faits.
- Changer la structure et le wording.
- Ne PAS extraire de news à ce stade.
- Produire UN SEUL bloc: un titre + un paragraphe.
- Format attendu dans rewrite_text:
  Titre
  Paragraphe
- Si le texte est trop court ou ambigu, poser des questions.

SORTIE JSON STRICTE
{
  "rewrite_text": "...",
  "needs_clarification": true|false,
  "questions": ["question 1", "question 2"]
}

RÈGLES DE SORTIE
- Retourne UNIQUEMENT du JSON valide.
- Si tout est clair : needs_clarification = false et questions = [].
"""
