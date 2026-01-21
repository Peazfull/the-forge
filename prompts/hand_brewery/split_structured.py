PROMPT_SPLIT_STRUCTURED = """
MISSION
Tu dois identifier et isoler CHAQUE news contenue dans un article reformulé.

RÈGLES
- Ne PAS fusionner des news différentes.
- Chaque news est autonome.
- Chaque news contient 1+ sections avec titre + contenu.
- Si l’IA hésite entre 1 ou plusieurs news, poser des questions.

FORMAT LOGIQUE
structured_news = [
  {
    "sections": [
      { "title": "...", "content": "..." },
      { "title": "...", "content": "..." }
    ]
  }
]

SORTIE JSON STRICTE
{
  "structured_news": [
    {
      "sections": [
        { "title": "...", "content": "..." }
      ]
    }
  ],
  "needs_clarification": true|false,
  "questions": ["question 1", "question 2"]
}

RÈGLES DE SORTIE
- Retourne UNIQUEMENT du JSON valide.
- Si tout est clair : needs_clarification = false et questions = [].
"""
