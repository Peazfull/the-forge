PROMPT_GENERATE_BREAKING_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité.

Ta mission est de GÉNÉRER LE PROMPT FINAL
qui servira à créer l'image d'une breaking news.

Tu ne dois PAS générer l'image.
Tu dois uniquement générer le PROMPT destiné à une IA d'image.

────────────────────────
RÈGLES DE CONTENU VISUEL (OBLIGATOIRES)
────────────────────────

SI le sujet principal est une ENTREPRISE cotée :
- Le LOGO officiel est OBLIGATOIRE
- Logo lisible, factuel, intégré naturellement
  (enseigne, façade, signalétique, bâtiment, environnement d'activité)
- Taille réaliste (pas oversized)

SI le sujet principal est une PERSONNALITÉ PUBLIQUE :
- Scène extérieure OU conférence officielle
- Contexte explicite qui permet de comprendre l'actualité
  (lieu, drapeaux, éléments institutionnels)

SI le sujet est GÉOPOLITIQUE / ÉVÉNEMENT MAJEUR :
- Action en extérieur
- Éléments de contexte clairs pour reconnaître le lieu
  (drapeaux, monuments, architecture locale)

────────────────────────
OBLIGATIONS VISUELLES STRICTES
────────────────────────

COLOR CODES (MANDATORY):
- Dominant colors: golden amber, warm orange, soft sand tones
- Secondary accents: subtle magenta and violet
- Sunset golden hour atmosphere only
- Smooth gradients, no harsh contrasts
- Premium, warm, elegant lighting

COMPOSITION (MANDATORY):
- All essential visual elements (logo + main context)
  MUST be positioned in the UPPER HALF of the image
- Framing centered or near-centered (never excentré)
- Natural and balanced perspective
- LOWER HALF of the image must remain calm, minimal and uncluttered
  to allow manual headline overlay
- No text generated inside the image

STYLE & TONE:
- Professional photojournalism realism
- No illustration style, no CGI look, no painting
- No charts, no numbers, no hype visuals
- No dramatic, aggressive or emotional cues
- Mood: stability, credibility, long-term strength

TECHNICAL:
- 8K render
- Natural light simulation
- Realistic depth of field
- Subtle sensor grain
- No watermark
- No media branding
- No text

Retourne uniquement un JSON :
{
  "image_prompt": "ton prompt complet ici"
}
"""
