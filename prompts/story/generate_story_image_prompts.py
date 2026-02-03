PROMPT_GENERATE_STORY_IMAGE_PROMPT = """
Tu es un expert en prompt d'images. Génère un prompt pour une image réaliste et impactante
qui illustre la news. L'image DOIT être en 16:9 (horizontal).

CONTRAINTES VISUELLES :
- Contexte visuel cohérent avec l'actualité (lieu, objet, symbole, industrie).
- Si une entreprise est citée : intégrer un logo OFFICIEL, discret et bien intégré.
- Si une personnalité / événement géopolitique : inclure un élément contextuel clair.
- Pas de texte, pas de watermark.
- Composition claire, sujet principal identifiable, action dans la moitié haute.
- Palette dominante : sunset stylized sky avec bleu, magenta et orange.
- Style photo réaliste, lumière cinématographique.
- Retourne uniquement un JSON strict.

FORMAT JSON :
{
  "image_prompt": "..."
}
"""
