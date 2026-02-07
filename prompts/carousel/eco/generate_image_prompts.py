PROMPT_GENERATE_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d’actualité économique, politique ou institutionnelle.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL
destiné à une IA de génération d’images.
Tu ne génères PAS l’image.

Le prompt doit illustrer l’ACTU MAJEURE,
en respectant strictement les contraintes visuelles ci-dessous.

────────────────────────
ACTU MAJEURE (OBLIGATOIRE)
────────────────────────

À partir du titre et du contenu :
- identifie l’ACTU MAJEURE qui porte l’information centrale
- conserve le contexte, mais hiérarchise clairement

Sélectionne LE SUJET VISUEL CENTRAL :
- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT ÉCONOMIQUE OU INSTITUTIONNEL

L’image doit illustrer :
→ l'entreprise, l’acteur ou le lieu qui porte l’action principale

────────────────────────
RÈGLE VISUELLE MAJEURE (NON NÉGOCIABLE)
────────────────────────

L’ACTION VISUELLE PRINCIPALE
DOIT OBLIGATOIREMENT ÊTRE SITUÉE
DANS LA MOITIÉ HAUTE DE L’IMAGE.

La MOITIÉ BASSE doit rester calme,
propre,
sans élément fort,

Personnages secondaires autorisés uniquement :
- silhouettes très lointaines et discrètes.

────────────────────────
RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI LE SUJET EST UNE ENTREPRISE :
- LE LOGO OFFICIEL RÉEL EST OBLIGATOIRE (très important)
- Image INVALIDE sans logo officiel visible
- Logo authentique et réel (pas une invention), lisible, intégré naturellement
- Contexte photographique réaliste : façade de bâtiment avec enseigne, siège social réel, environnement professionnel photographié
- Le logo doit apparaître comme sur une vraie photo (enseigne, façade, signalétique)
- INTERDIT : logos inventés, stylisés, flottants ou artificiels

SI LE SUJET EST UNE PERSONNALITÉ PUBLIQUE :
- SEULEMENT si la personnalité est le CŒUR de l'actualité (pas juste mentionnée)
- Uniquement personnalité publique réelle et très connue (PDG, ministre, président, etc.)
- Contexte photo de presse OBLIGATOIRE :
  conférence officielle, intervention publique, déplacement institutionnel
- Posture calme, neutre, maîtrisée (pas de mise en scène dramatique)
- Rendu photographique réaliste (comme une photo Reuters/AFP)
- SI la personnalité n'est PAS le cœur de l'actu → utiliser le contexte entreprise/lieu à la place

SI LE SUJET EST UN LIEU / ÉVÉNEMENT :
- Éléments de reconnaissance OBLIGATOIRES (très important) :
  drapeaux, signalétique officielle, monument, architecture identifiable
- Contexte institutionnel clair et crédible

────────────────────────
DIRECTION ARTISTIQUE (OBLIGATOIRE)
────────────────────────

STYLE (ULTRA-PRIORITAIRE) :
- PHOTO DE PRESSE RÉELLE, pas une illustration
- Photojournalisme économique professionnel
- Rendu photographique 100% réaliste et authentique
- ABSOLUMENT AUCUN élément irréel, fictif ou stylisé
- INTERDIT : CGI, illustrations, dessins, graphiques, charts, infographies
- INTERDIT : éléments fantastiques, surréalistes ou impossibles dans le monde réel
- Le résultat doit ressembler à une photo prise par un photographe Reuters/AFP

PALETTE COULEURS OBLIGATOIRE :
- Stuning bright sky with sunset stylized sky colors: purple, Purple fluo, magenta tones
- Dominante : purple, orange, magenta tones
- Accents lumineux subtils et élégants

────────────────────────
COMPOSITION & TECHNIQUE
────────────────────────

- Sujet principal placé dans la MOITIÉ HAUTE
- Cadrage centré ou quasi centré
- Perspective naturelle et équilibrée
- Fond propre, non distrayant

Inclure explicitement :
- 8K render
- professional photojournalism style
- natural or high-end studio lighting
- realistic depth of field
- subtle natural sensor grain
- no text in image

────────────────────────
INTERDICTIONS CRITIQUES (ABSOLUMENT OBLIGATOIRE À RESPECTER)
────────────────────────

⚠️ CRITICAL : L'IMAGE DOIT ÊTRE UNE PHOTO PHOTOGRAPHIABLE PAR UN HUMAIN DANS LE MONDE RÉEL

ABSOLUMENT INTERDIT (IMAGE INVALIDE SI PRÉSENT) :
❌ NO TEXT whatsoever (no titles, no labels, no captions, no numbers, no legends, no annotations)
❌ NO CHARTS (no bar charts, no line graphs, no pie charts, no data visualizations)
❌ NO SCREENS showing data/graphics (no monitors displaying charts, no digital boards with statistics)
❌ NO INFOGRAPHICS (no diagrams, no flowcharts, no illustrated data)
❌ NO UI ELEMENTS (no interfaces, no dashboards, no control panels with data)
❌ NO TRADING SCREENS (no stock tickers, no market data, no financial graphs)
❌ NO OVERLAYS (no graphic overlays, no text boxes, no arrows, no highlights)
❌ NO ARTIFICIAL ELEMENTS (no CGI, no 3D renders, no impossible physics)

⚠️ EXEMPLES D'ÉLÉMENTS INTERDITS À MENTIONNER EXPLICITEMENT DANS LE PROMPT :
- "NO digital screens showing charts or data visualizations"
- "NO bar graphs, line graphs, or statistical displays in the image"
- "NO infographics or data dashboards visible anywhere"
- "The image must show ONLY physical, real-world elements that could be photographed"

SI UN DE CES ÉLÉMENTS APPARAÎT → L'IMAGE EST INVALIDE ET DOIT ÊTRE REJETÉE

────────────────────────
EXEMPLE D'OUTPUT ATTENDU (RÉFÉRENCE)
────────────────────────

Ultra-realistic editorial press photograph, 8K render, professional photojournalism style.

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
Sunset stylized sky with dominant purple, purple fluo, orange, and magenta tones.
Stunning sunset.
Atmosphere premium, stunning.

CRITICAL RESTRICTIONS (MANDATORY – MUST BE EXPLICITLY INCLUDED IN EVERY PROMPT)
NO digital screens displaying charts, graphs, or data visualizations.
NO bar charts, line graphs, pie charts, or statistical displays anywhere in the image.
NO infographics, dashboards, or data presentations visible.
NO text, numbers, labels, or captions of any kind.
The image must show ONLY physical, real-world elements photographable by a press photographer.
NO CGI, no 3D renders, no artificial overlays.

TECHNICAL REQUIREMENTS (MANDATORY)
Natural or high-end studio lighting.
Realistic depth of field.
Subtle natural sensor grain.
No text in image (critical)
No watermark.
No media logo.
No captions or overlays of any kind.

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
