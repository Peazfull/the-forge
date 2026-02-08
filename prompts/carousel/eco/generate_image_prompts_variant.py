PROMPT_GENERATE_IMAGE_PROMPT_VARIANT = """
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

⚠️ COMPOSITION VERTICALE OBLIGATOIRE (ULTRA-CRITIQUE) :

L'image doit être UNE SEULE ET UNIQUE PHOTOGRAPHIE COHÉRENTE.
INTERDIT ABSOLU : diviser l'image en deux parties distinctes (haut/bas).

PERSPECTIVE OBLIGATOIRE :
- Photo prise en CONTRE-PLONGÉE (low-angle shot, vue d'en bas vers le haut)
- Le photographe est positionné au sol ou en position basse
- L'appareil photo est orienté vers le HAUT
- Cette perspective naturelle place automatiquement les éléments importants dans le tiers supérieur

PLACEMENT DES ÉLÉMENTS CLÉS :
- Logo sur bâtiment, personnalité, ou lieu → positionnés dans le TIERS SUPÉRIEUR de l'image
- Résultat naturel de la prise de vue en contre-plongée
- Le reste de l'image (partie basse) = continuité naturelle de la même scène (sol, base du bâtiment, environnement proche)

UNITÉ VISUELLE OBLIGATOIRE :
- UNE SEULE photo continue, pas deux images collées
- Perspective et lumière cohérentes sur toute la hauteur
- Transition fluide du bas vers le haut de l'image

La PARTIE BASSE doit rester calme, propre, sans élément fort,

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

PERSPECTIVE ET CADRAGE (ULTRA-CRITIQUE) :
- LOW-ANGLE SHOT (contre-plongée) OBLIGATOIRE
- Camera positioned LOW, pointing UPWARD
- Single continuous photograph from one vantage point
- Key elements (logo, person, landmark) naturally positioned in UPPER THIRD due to low angle
- Lower portion = natural ground level, base of building, immediate surroundings
- NO split composition, NO two separate images merged together
- Seamless visual flow from bottom to top

COHÉRENCE VISUELLE :
- ONE unified photograph, not a collage
- Consistent lighting across entire image
- Natural perspective from single camera position
- Fluid transition throughout the frame
- Cadrage centré ou quasi centré
- Fond propre, non distrayant

Inclure explicitement dans le prompt :
- "low-angle shot" ou "contre-plongée"
- "camera positioned at ground level pointing upward"
- "single continuous photograph"
- "natural perspective with key elements in upper third"
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
❌ NO SPLIT IMAGES (no top/bottom divided compositions, no collage of two separate photos)
❌ NO HORIZONTAL DIVISIONS (the image must be one continuous scene, not two stacked images)

⚠️ EXEMPLES D'ÉLÉMENTS INTERDITS À MENTIONNER EXPLICITEMENT DANS LE PROMPT :
- "NO digital screens showing charts or data visualizations"
- "NO bar graphs, line graphs, or statistical displays in the image"
- "NO infographics or data dashboards visible anywhere"
- "NO split composition or two separate images merged together"
- "Single continuous photograph from one camera position"
- "The image must show ONLY physical, real-world elements that could be photographed"

SI UN DE CES ÉLÉMENTS APPARAÎT → L'IMAGE EST INVALIDE ET DOIT ÊTRE REJETÉE

────────────────────────
EXEMPLE D'OUTPUT ATTENDU (RÉFÉRENCE)
────────────────────────

Ultra-realistic editorial press photograph, 8K render, professional photojournalism style.

SUBJECT (MANDATORY)
A major European technology company as the single central subject, illustrated through their corporate headquarters.
The image must represent corporate innovation and business growth, focusing on the company's physical presence.

ACTION & COMPOSITION (MANDATORY)
LOW-ANGLE SHOT (contre-plongée) – camera positioned at ground level, pointing upward toward the building.
This natural perspective places the main visual action and all major elements in the UPPER THIRD of the image.
The lower portion of the image shows the natural ground-level environment (pavement, entrance area, immediate surroundings).
CRITICAL: This must be ONE single continuous photograph, NOT two separate images.
Seamless visual unity from bottom to top, consistent lighting and perspective throughout.
The lower third remains clean, uncluttered, and flows naturally from the upper composition.
Centered or near-centered framing with natural, balanced perspective.

CONTEXT (MANDATORY – CORPORATE ENVIRONMENT)
Modern corporate headquarters setting.
OBLIGATORY visual identifiers:
- Authentic, REAL company logo prominently displayed on the building facade (official signage, enseigne)
- Contemporary office building architecture
- Professional business environment photographed from exterior
- Clean, premium corporate aesthetic
No generic or invented logos – the logo must appear as it would in real press photography.

PEOPLE (STRICT)
No visible individuals in the foreground.
If present, only very distant, discreet silhouettes allowed.

ART DIRECTION (MANDATORY)
Sunset stylized sky with dominant purple, purple fluo, orange, and magenta tones.
Stunning sunset backdrop behind the building.
Atmosphere premium, stunning, corporate yet aspirational.

CRITICAL RESTRICTIONS (MANDATORY – MUST BE EXPLICITLY INCLUDED IN EVERY PROMPT)
Low-angle shot (contre-plongée) with camera at ground level.
Single continuous photograph, NOT two separate images or split composition.
NO digital screens displaying charts, graphs, or data visualizations.
NO bar charts, line graphs, pie charts, or statistical displays anywhere in the image.
NO infographics, dashboards, or data presentations visible.
NO horizontal division or top/bottom split – must be one unified scene.
NO text, numbers, labels, or captions of any kind.
The image must show ONLY physical, real-world elements photographable by a press photographer.
NO CGI, no 3D renders, no artificial overlays.
Seamless visual flow with consistent perspective and lighting throughout.

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
