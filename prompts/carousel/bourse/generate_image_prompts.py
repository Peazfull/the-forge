PROMPT_GENERATE_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité économique, politique ou institutionnelle.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL
destiné à une IA de génération d'images.
Tu ne génères PAS l'image.

Le prompt doit illustrer l'ACTU MAJEURE,
en respectant strictement les contraintes visuelles ci-dessous.

────────────────────────
ACTU MAJEURE (OBLIGATOIRE)
────────────────────────

À partir du titre et du contenu :
- identifie l'ACTU MAJEURE qui porte l'information centrale
- conserve le contexte, mais hiérarchise clairement

Sélectionne LE SUJET VISUEL CENTRAL :
- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT ÉCONOMIQUE OU INSTITUTIONNEL

L'image doit illustrer :
→ l'entreprise, l'acteur ou le lieu qui porte l'action principale

────────────────────────
RÈGLE VISUELLE MAJEURE (NON NÉGOCIABLE)
────────────────────────

L'ACTION VISUELLE PRINCIPALE
DOIT OBLIGATOIREMENT ÊTRE SITUÉE
DANS LA MOITIÉ HAUTE DE L'IMAGE.

La MOITIÉ BASSE doit rester calme,
propre,
sans élément fort,

Personnages secondaires autorisés uniquement :
- silhouettes très lointaines et discrètes.

────────────────────────
RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI LE SUJET EST UNE ENTREPRISE :
- LE LOGO OFFICIEL EST OBLIGATOIRE (très important)
- Image INVALIDE sans logo officiel visible
- Logo authentique, RÉEL, lisible, intégré naturellement dans un contexte photographique réaliste
- Contexte : façade, siège, environnement professionnel réel

SI LE SUJET EST UNE PERSONNALITÉ PUBLIQUE :
- Uniquement personnalité publique connue ET SEULEMENT si elle est le CŒUR de l'actualité
- Contexte OBLIGATOIRE :
  conférence officielle, intervention publique ou déplacement institutionnel
- Posture calme, neutre, maîtrisée
- Style PHOTO DE PRESSE RÉELLE

SI LE SUJET EST UN LIEU / ÉVÉNEMENT :
- Éléments de reconnaissance OBLIGATOIRES (très important) :
  drapeaux, signalétique officielle, monument, architecture identifiable
- Contexte institutionnel clair et crédible

────────────────────────
INTERDICTIONS CRITIQUES ⛔
────────────────────────

🚫 AUCUN écran affichant des graphiques, données, charts
🚫 AUCUN graphique de trading, courbe boursière, infographie
🚫 AUCUN dashboard, tableau de bord, visualisation de données
🚫 AUCUN élément CGI, illustration, dessin, style artistique
🚫 AUCUN texte visible (titres, labels, légendes)
🚫 AUCUN watermark, logo média, overlay

→ L'image doit montrer UNIQUEMENT des éléments physiques et réels du monde réel

────────────────────────
DIRECTION ARTISTIQUE (OBLIGATOIRE)
────────────────────────

STYLE :
- Ultra-realistic editorial PRESS PHOTOGRAPH (PHOTO DE PRESSE RÉELLE)
- Photojournalisme économique
- Photo de presse réaliste, authentique, crédible
- IMITATION PHOTO DE PRESSE
- Aucun style illustratif, artistique ou CGI

PALETTE COULEURS OBLIGATOIRE :
- Stunning bright sky with sunset stylized sky colors: cyan bleu, fluo bleu, magenta tones
- Dominante : cyan bleu, orange, magenta tones
- Accents lumineux subtils et élégants

────────────────────────
COMPOSITION & TECHNIQUE
────────────────────────

- Sujet principal placé dans la MOITIÉ HAUTE
- Cadrage centré ou quasi centré
- Perspective naturelle et équilibrée
- Fond propre, non distrayant

Inclure explicitement dans le prompt que tu génères :
- 8K render
- professional photojournalism style
- natural or high-end studio lighting
- realistic depth of field
- subtle natural sensor grain
- no text in image

ET ces NEGATIVE PROMPTS obligatoires :
- ABSOLUTELY NO TEXT in image (no titles, no labels, no captions)
- NO SCREENS showing data/graphics (no digital displays with charts or visualizations)
- NO CHARTS, NO INFOGRAPHICS, NO DASHBOARDS (no bar graphs, line graphs, or statistical displays)
- No fictional elements or overlays (no trading charts, no UI screens, no data graphics)
- No surreal or impossible elements (must be realistic in the real world)
- The image must show ONLY physical, real-world elements
- no watermark
- no media logo
- no captions
- no overlays

────────────────────────
EXEMPLE D'OUTPUT ATTENDU (RÉFÉRENCE)
────────────────────────

Ultra-realistic editorial PRESS PHOTOGRAPH, 8K render, professional photojournalism style.

SUBJECT (MANDATORY)
France as the single central subject, illustrated through a PUBLIC HEALTH AND FOOD SAFETY INSTITUTIONAL CONTEXT.
The image must represent the strengthening of sanitary regulations for infant milk in France, not the product itself.

ACTION & COMPOSITION (MANDATORY)
The main visual action and all major elements must be strictly positioned in the UPPER HALF of the image.
The LOWER HALF must remain calm, clean, and uncluttered, designed to receive text overlay.
Centered or near-centered framing with a natural, balanced perspective.

CONTEXT (MANDATORY – LOCATION & SYMBOLS)
Institutional and regulatory setting linked to French public health and food safety authorities.
OBLIGATORY visual identifiers:
- French flags
- Official government or public health building (ministry, regulatory institution, or inspection facility)
- Clean, sterile, professional environment suggesting health regulation and safety
No product marketing, no brands, no emotional symbolism.

PEOPLE (STRICT)
No visible individuals in the foreground.
If present, only very distant, discreet silhouettes allowed.

ART DIRECTION (MANDATORY)
Sunset stylized sky with dominant cyan bleu, fluo bleu, orange, and magenta tones.
Stunning sunset.
Atmosphere premium, stunning.
PRESS PHOTO realistic style.

TECHNICAL REQUIREMENTS (MANDATORY)
Natural or high-end studio lighting.
Realistic depth of field.
Subtle natural sensor grain.
No text in image (important)
No watermark.
No media logo.
No captions or overlays.

NEGATIVE PROMPTS (CRITICAL):
NO digital screens displaying charts or data visualizations.
NO bar graphs, line graphs, or statistical displays.
The image must show ONLY physical, real-world elements photographed in a press context.

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
