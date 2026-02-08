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

PALETTE COULEURS OBLIGATOIRE (très important car DA sur projet) :
- Stunning bright sky with sunset stylized sky colors: cyan bleu, fluo bleu, orange and magenta tones
- Dominante : cyan bleu, fluo bleu, orange, magenta tones
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

Inclure explicitement dans le prompt que tu génères :
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
Tesla as the single central subject, illustrated through their corporate headquarters and brand identity.
The image must represent a specific business event: quarterly earnings announcement, production milestone, market expansion, or strategic partnership.
Example context: "Tesla announces record quarterly deliveries" or "Tesla opens new Gigafactory in Europe".

ACTION & COMPOSITION (MANDATORY)
LOW-ANGLE SHOT (contre-plongée) – camera positioned at ground level, pointing upward toward the building.
This natural perspective places the main visual action and all major elements in the UPPER THIRD of the image.
The lower portion of the image shows the natural ground-level environment (pavement, entrance area, immediate surroundings).
CRITICAL: This must be ONE single continuous photograph, NOT two separate images.
Seamless visual unity from bottom to top, consistent lighting and perspective throughout.
The lower third remains clean, uncluttered, and flows naturally from the upper composition.
Centered or near-centered framing with natural, balanced perspective.

CONTEXT (MANDATORY – CORPORATE ENVIRONMENT)
Tesla headquarters, Gigafactory, or corporate facility.
OBLIGATORY visual identifiers:
- Authentic TESLA logo prominently displayed on the building facade (official signage, official Tesla "T" logo)
- Modern automotive/technology facility or corporate building architecture
- Professional business environment photographed from exterior
- Clean, premium corporate aesthetic suggesting innovation and market leadership
The logo must appear as it would in real financial press photography covering Tesla earnings or announcements (Bloomberg, Reuters, Financial Times).

PEOPLE (STRICT)
No visible individuals in the foreground.
If present, only very distant, discreet silhouettes allowed.

ART DIRECTION (MANDATORY)
Sunset stylized sky with dominant cyan bleu, fluo bleu, orange, and magenta tones.
Stunning sunset backdrop behind the corporate building.
Atmosphere premium, stunning, financial and aspirational.
PRESS PHOTO realistic style (financial journalism quality).

CRITICAL RESTRICTIONS (MANDATORY – MUST BE EXPLICITLY INCLUDED IN EVERY PROMPT)
Low-angle shot (contre-plongée) with camera at ground level.
Single continuous photograph, NOT two separate images or split composition.
NO digital screens displaying charts, graphs, or data visualizations.
NO bar charts, line graphs, pie charts, or statistical displays anywhere in the image.
NO stock market tickers, trading screens, or financial dashboards visible.
NO infographics, dashboards, or data presentations visible.
NO horizontal division or top/bottom split – must be one unified scene.
NO text, numbers, labels, or captions of any kind.
The image must show ONLY physical, real-world elements photographable by a financial press photographer.
NO CGI, no 3D renders, no artificial overlays.
Seamless visual flow with consistent perspective and lighting throughout.

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
