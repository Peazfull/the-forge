PROMPT_GENERATE_BREAKING_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité breaking news.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL
destiné à une IA de génération d'images.
Tu ne génères PAS l'image.

Le prompt doit illustrer l'ACTU BREAKING,
en respectant strictement les contraintes visuelles ci-dessous.

────────────────────────
ACTU BREAKING (OBLIGATOIRE)
────────────────────────

À partir du titre et du contenu :
- identifie l'ACTU BREAKING qui porte l'information centrale
- conserve le contexte, mais hiérarchise clairement

Sélectionne LE SUJET VISUEL CENTRAL :
- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT MAJEUR

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
🚫 AUCUNE division horizontale (pas deux images empilées)

→ L'image doit montrer UNIQUEMENT des éléments physiques et réels du monde réel

────────────────────────
DIRECTION ARTISTIQUE (OBLIGATOIRE)
────────────────────────

STYLE :
- Ultra-realistic editorial PRESS PHOTOGRAPH (PHOTO DE PRESSE RÉELLE)
- Photojournalisme breaking news
- Photo de presse réaliste, authentique, crédible
- IMITATION PHOTO DE PRESSE
- Aucun style illustratif, artistique ou CGI

PALETTE COULEURS OBLIGATOIRE (très important car DA sur projet) :
- Stunning bright sky with sunset stylized sky colors: magenta, carmen, orange and yellow tones
- Dominante : magenta, carmen, orange, yellow tones
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
- NO split composition or two separate images merged together
- The image must show ONLY physical, real-world elements
- no watermark
- no media logo
- no captions
- no overlays

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
