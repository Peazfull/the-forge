PROMPT_GENERATE_CAROUSEL_CAPTION = """
Tu es un expert social media. Génère une caption Instagram pour un carrousel d'actualités économiques.

CONTRAINTES :
- Ne pas recopier les textes des slides.
- Reformuler chaque actu sous forme de mini-titre impactant (entre le titre et un court paragraphe).
- Ton clair, punchy, informatif.
- Format final : un texte fluide avec des sauts de ligne.
- Termine par un CTA EXACT :
  "Rejoignez la liste d'attente pour notre future newsletter 100% gratuite (lien en bio)."
- AUCUN markdown (pas de **, pas d'italique, pas de code).
- Mets 1 emoji au début de chaque mini-titre, et aucun emoji ailleurs dans la ligne.

FORMAT :
- 1 ligne d'accroche avec "Rejoignez la liste d'attente pour notre future newsletter 100% gratuite (lien en bio)"
- Une liste de 4 à 8 mini-titres (1 par actu).
- Puis le CTA final : "Partagez et réagissez !"
Ne retourne que le texte final (pas de JSON).
"""
