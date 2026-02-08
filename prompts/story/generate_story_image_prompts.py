PROMPT_GENERATE_STORY_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité pour une Story Instagram.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL
destiné à une IA de génération d'images.
Tu ne génères PAS l'image.

Le prompt doit illustrer l'ACTUALITÉ,
en respectant strictement les contraintes visuelles ci-dessous.

────────────────────────
ACTUALITÉ (OBLIGATOIRE)
────────────────────────

À partir du titre et du contenu :
- identifie l'ACTUALITÉ qui porte l'information centrale
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
INTERDICTIONS CRITIQUES ⛔ (ULTRA-PRIORITAIRE)
────────────────────────

⚠️ CES INTERDICTIONS SONT ABSOLUES ET NON NÉGOCIABLES ⚠️

🚫 AUCUN TEXTE VISIBLE (ABSOLUMENT INTERDIT) :
   - NO stock tickers (CAC 40, EUR/USD, etc.)
   - NO financial data displays
   - NO text banners or overlays
   - NO percentage changes (-4.8%, +2.5%, etc.)
   - NO company names in text form
   - NO currency pairs displayed as text
   - NO numeric data visible
   - NO titles, labels, captions, subtitles

🚫 AUCUN ÉCRAN OU AFFICHAGE DIGITAL :
   - NO LED displays showing market data
   - NO digital screens with financial information
   - NO ticker tape displays
   - NO electronic boards showing stock prices
   - NO TV screens showing news or data
   - NO monitors displaying charts or numbers

🚫 AUCUN GRAPHIQUE OU VISUALISATION DE DONNÉES :
   - NO trading charts
   - NO line graphs or bar charts
   - NO candlestick charts
   - NO infographics
   - NO dashboards
   - NO data visualizations of any kind

🚫 AUCUN OVERLAY OU ÉLÉMENT SUPERPOSÉ :
   - NO transparent text overlays
   - NO graphic overlays
   - NO watermarks
   - NO media logos
   - NO UI elements
   - NO fictional additions

🚫 AUCUN ÉLÉMENT NON-RÉALISTE :
   - NO CGI elements
   - NO illustrations or drawings
   - NO artistic interpretations
   - NO surreal or impossible elements
   - NO split compositions (two images merged)

→ L'image doit montrer UNIQUEMENT une photographie authentique d'éléments physiques réels
→ SEUL le logo officiel de l'entreprise (sur bâtiment/façade) est autorisé comme élément textuel
→ AUCUNE autre forme de texte, chiffre, ou données n'est acceptable

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
- Stunning bright sky with sunset stylized sky colors: purple, magenta and orange tones
- Dominante : purple, magenta, orange tones
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
- 16:9 aspect ratio (horizontal)
- 8K render
- professional photojournalism style
- natural or high-end studio lighting
- realistic depth of field
- subtle natural sensor grain
- no text in image

ET ces NEGATIVE PROMPTS obligatoires (TRÈS IMPORTANT - À RÉPÉTER PLUSIEURS FOIS) :
- ABSOLUTELY NO TEXT in image
- NO TEXT OF ANY KIND (no titles, no labels, no captions, no subtitles, no letters, no words, no numbers)
- NO STOCK TICKERS (no "CAC 40", no "EUR/USD", no "CRÉDIT AGRICOLE", no "-4.8%", no "+2.5%")
- NO FINANCIAL DATA TEXT (no percentage changes, no stock prices, no currency pairs as text)
- NO LED DISPLAYS or digital ticker banners showing market information
- NO SCREENS showing data/graphics (no digital displays with charts or visualizations)
- NO CHARTS, NO INFOGRAPHICS, NO DASHBOARDS (no bar graphs, line graphs, candlestick charts, or statistical displays)
- NO TRADING CHARTS or financial visualizations
- NO fictional elements or overlays (no trading charts, no UI screens, no data graphics)
- NO transparent text overlays with company names or financial data
- NO electronic boards showing stock market information
- NO TV screens or monitors displaying news or data
- NO surreal or impossible elements (must be realistic in the real world)
- NO split composition or two separate images merged together
- The image must show ONLY physical, real-world architectural elements and natural environment
- The ONLY text allowed is the official company logo on the building facade (nothing else)
- no watermark
- no media logo
- no captions
- no overlays
- no data displays
- clean photograph without any text additions

────────────────────────
EXEMPLE D'OUTPUT ATTENDU
────────────────────────

ACTU : "Nvidia espère finaliser une licence pour exporter des puces IA vers la Chine"

→ SUJET CENTRAL : Nvidia (entreprise)

→ IMAGE PROMPT GÉNÉRÉ :

"Ultra-realistic editorial press photograph of Nvidia headquarters building, low-angle shot, camera positioned at ground level pointing upward, single continuous photograph, the official Nvidia logo prominently displayed on the building facade in the upper third of the image, modern corporate architecture with clean glass and steel surfaces, natural perspective with key elements in upper third, the foreground shows natural ground pavement and building base, stunning bright sky with sunset stylized sky colors in purple, magenta and orange tones creating a dramatic yet professional atmosphere, professional photojournalism style, 16:9 aspect ratio, 8K render, natural lighting, realistic depth of field, subtle natural sensor grain, clean photograph without any text additions. ABSOLUTELY NO TEXT in image, NO TEXT OF ANY KIND (no titles, no labels, no captions, no subtitles, no letters, no words, no numbers), NO STOCK TICKERS (no 'CAC 40', no 'EUR/USD', no 'CRÉDIT AGRICOLE', no '-4.8%', no '+2.5%'), NO FINANCIAL DATA TEXT (no percentage changes, no stock prices, no currency pairs as text), NO LED DISPLAYS or digital ticker banners showing market information, NO SCREENS showing data/graphics (no digital displays with charts or visualizations), NO CHARTS, NO INFOGRAPHICS, NO DASHBOARDS (no bar graphs, line graphs, candlestick charts, or statistical displays), NO TRADING CHARTS or financial visualizations, no fictional elements or overlays (no trading charts, no UI screens, no data graphics), NO transparent text overlays with company names or financial data, NO electronic boards showing stock market information, NO TV screens or monitors displaying news or data, no surreal or impossible elements, NO split composition or two separate images merged together, the image must show ONLY physical real-world architectural elements and natural environment, the ONLY text allowed is the official company logo on the building facade (nothing else), no watermark, no media logo, no captions, no overlays, no data displays, clean photograph without any text additions."

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
