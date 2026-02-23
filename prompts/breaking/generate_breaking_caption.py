PROMPT_GENERATE_BREAKING_CAPTION = """
Tu es un expert social media. Génère une caption Instagram pour un Breaking News.

CONTRAINTES :
- Ne pas recopier le texte du slide.
- Reformuler en mini-titre impactant (entre le titre et un court paragraphe).
- Ton clair, punchy, informatif.
- Format final : un texte fluide avec des sauts de ligne.
- Termine par un CTA EXACT cité en exemple ci dessous. 
- AUCUN markdown (pas de **, pas d'italique, pas de code).
- Mets 1 emoji au début de la ligne du mini-titre, et aucun emoji ailleurs.

FORMAT :
- Une seule ligne de mini-titre (Breaking)
- 1 ligne. "Rejoignez la liste d'attente pour notre future newsletter 100% gratuite (lien en bio)"
- Puis le CTA final : "#finamonrolls, c'est toute l'actu éco, bourse, PEA, crypto en 1 min par jour, Active la cloche pour être toujours informé(e)"
Ne retourne que le texte final (pas de JSON).
"""
