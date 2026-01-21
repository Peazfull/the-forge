PROMPT_EXTRACT_NEWS = """
MISSION
Tu dois identifier et isoler les news réellement distinctes contenues dans un article reformulé.

CONTRAINTES
- Si plusieurs paragraphes parlent du MEME sujet, garde UNE seule news.
- Ne sépare que si les sujets sont clairement différents.
- Chaque news doit être autonome.
- Une news peut contenir plusieurs sections.
- Chaque section DOIT contenir un titre clair et un contenu explicatif.
- Si tu hésites entre 1 ou plusieurs news, pose une question.

STRUCTURE DE SORTIE (JSON STRICT)
{
  "structured_news": [
    {
      "sections": [
        {"title": "Titre", "content": "Paragraphe associé"}
      ]
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
