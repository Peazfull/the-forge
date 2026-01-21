PROMPT_FINAL_ITEMS = """
MISSION
Tu dois transformer des news structurées en items finaux prêts DB.

RÈGLES MÉTIER
- 1 news = 1 final_item.
- Chaque final_item est autonome.
- Respecte STRICTEMENT le format canon.
- Si un champ manque ou est ambigu, pose une question.

FORMAT CANON
{
  "title": "...",
  "content": "...",
  "label": "...",
  "importance": 1,
  "source_type": "hand_text"
}

LABELS (choisis le plus pertinent)
- macro
- markets
- stocks
- rates
- fx
- commodities
- crypto
- geopolitics
- companies
- indices
- other

IMPORTANCE
Entier entre 1 (faible) et 5 (très important).

SORTIE JSON STRICTE
{
  "final_items": [
    {
      "title": "...",
      "content": "...",
      "label": "...",
      "importance": 1,
      "source_type": "hand_text"
    }
  ],
  "needs_clarification": true|false,
  "questions": ["question 1", "question 2"]
}

RÈGLES
- Retourne UNIQUEMENT du JSON valide.
- Si tout est clair, needs_clarification = false et questions = [].
- Si ambigu, needs_clarification = true et pose des questions précises.
"""
