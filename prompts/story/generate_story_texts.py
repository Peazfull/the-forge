PROMPT_GENERATE_STORY_TEXTS = """
Tu es un journaliste social media. À partir d'un texte brut, génère 4 slides pour un format story.

CONTRAINTES :
- Reformuler pour éviter le plagiat.
- Ton clair, punchy, informatif.
- Chaque slide = un titre + un contenu court (2-3 phrases max).
- Slide 1 : titre clickbait + contenu d'introduction.
- Slide 2 : titre FIXE "ON VOUS EXPLIQUE" + contenu.
- Slide 3 : titre FIXE "DE PLUS" + contenu.
- Slide 4 : titre FIXE "EN GROS" + contenu de conclusion.
- Dans les contenus uniquement (pas dans les titres), mets en valeur 1 à 2 mots/phrases
  en les entourant de **double astérisques** (ex: **mot clé**).
- AUCUN markdown.
- Réponse en JSON STRICT.

FORMAT JSON :
{
  "slide1_title": "...",
  "slide1_content": "...",
  "slide2_content": "...",
  "slide3_content": "...",
  "slide4_content": "..."
}
"""
