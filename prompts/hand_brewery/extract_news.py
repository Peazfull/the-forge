PROMPT_EXTRACT_NEWS = """
MISSION
Tu dois identifier et isoler TOUS les sujets d'information financiers distincts contenus dans un article reformulé.

CONTRAINTES
- Ne fusionne PAS des sujets différents.
- Ne hiérarchise PAS : inclure aussi les sujets secondaires.
- Si plusieurs paragraphes parlent du MÊME sujet, garde UNE seule news.
- Sépare dès qu'il y a un changement clair de sujet (entreprises, macro, taux, indices, crypto, etc.).
- Chaque news doit être autonome.
- Chaque news contient 1 seul bloc : un titre clair + un paragraphe explicatif.

FORMAT ATTENDU (TEXTE BRUT)
Titre 1
Paragraphe lié au titre 1.

Titre 2
Paragraphe lié au titre 2.

RÈGLES
- Retourne UNIQUEMENT du texte brut.
- Ne retourne PAS de JSON.
- Ne retourne PAS de markdown.
"""
