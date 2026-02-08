PROMPT_GENERATE_STORY_IMAGE_PROMPT = """
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
⛔ INTERDICTIONS ABSOLUES (À LIRE EN PREMIER) ⛔
────────────────────────

❌ INTERDIT DE GÉNÉRER :
- "stock market screen showing..."
- "LED display with financial data..."
- "digital ticker showing stock prices..."
- "electronic board displaying market information..."
- "chart showing decline/growth..."
- "graph illustrating performance..."
- "data visualization of..."
- "trading screen with..."
- ANY mention of charts, graphs, screens, displays, data visualizations

✅ CE QU'ON VEUT :
- "corporate building with official logo on facade..."
- "headquarters exterior with company signage..."
- "business facility photographed from low angle..."
- "architectural shot of corporate headquarters..."

────────────────────────
RÈGLE VISUELLE MAJEURE (NON NÉGOCIABLE)
────────────────────────

⚠️ COMPOSITION VERTICALE OBLIGATOIRE (ULTRA-CRITIQUE) :

L'image doit être UNE SEULE ET UNIQUE PHOTOGRAPHIE COHÉRENTE D'UN BÂTIMENT.
INTERDIT ABSOLU : diviser l'image en deux parties distinctes (haut/bas).

PERSPECTIVE OBLIGATOIRE :
- Photo prise en CONTRE-PLONGÉE (low-angle shot, vue d'en bas vers le haut)
- Le photographe est positionné au sol ou en position basse
- L'appareil photo est orienté vers le HAUT VERS LE BÂTIMENT
- Cette perspective naturelle place automatiquement les éléments importants dans le tiers supérieur

PLACEMENT DES ÉLÉMENTS CLÉS DANS LE TIERS SUPÉRIEUR :
⚠️ ATTENTION : "tiers supérieur" signifie :
✅ Logo officiel sur la FAÇADE DU BÂTIMENT
✅ Signalétique architecturale du siège social
✅ Architecture du bâtiment avec branding visible
❌ PAS un écran LED avec données boursières
❌ PAS un ticker électronique
❌ PAS un panneau d'affichage digital

UNITÉ VISUELLE OBLIGATOIRE :
- UNE SEULE photo continue d'un bâtiment, pas deux images collées
- Perspective et lumière cohérentes sur toute la hauteur
- Transition fluide du bas vers le haut de l'image

La PARTIE BASSE doit rester calme, propre, sans élément fort :
- Sol, pavement, base du bâtiment
- PAS de personnages au premier plan (flous ou nets)
- Seulement silhouettes très lointaines et discrètes si nécessaire

────────────────────────
RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI LE SUJET EST UNE ENTREPRISE :
- LE LOGO OFFICIEL SUR LA FAÇADE DU BÂTIMENT EST OBLIGATOIRE (très important)
- Image INVALIDE sans logo officiel visible SUR LE BÂTIMENT
- Logo authentique, RÉEL, lisible, intégré naturellement sur l'ARCHITECTURE du bâtiment
- Contexte : FAÇADE du siège social, EXTÉRIEUR du bâtiment, environnement professionnel réel
- ❌ PAS un écran LED/digital montrant le nom de l'entreprise
- ❌ PAS un ticker électronique avec le cours de l'action
- ✅ OUI le logo officiel fixé/peint/gravé sur la FAÇADE physique du bâtiment

EXEMPLE VALIDE : "Tesla headquarters building with official Tesla 'T' logo mounted on the building facade"
EXEMPLE INVALIDE : "LED screen displaying 'TESLA' stock price and chart"

SI LE SUJET EST UNE PERSONNALITÉ PUBLIQUE :
- Uniquement personnalité publique connue ET SEULEMENT si elle est le CŒUR de l'actualité
- Contexte OBLIGATOIRE :
  conférence officielle, intervention publique ou déplacement institutionnel
- Posture calme, neutre, maîtrisée
- Style PHOTO DE PRESSE RÉELLE
- ❌ PAS de personnages marchant au premier plan (comme dans l'image interdite)

SI LE SUJET EST UN LIEU / ÉVÉNEMENT :
- Éléments de reconnaissance OBLIGATOIRES (très important) :
  drapeaux, signalétique officielle, monument, architecture identifiable
- Contexte institutionnel clair et crédible

────────────────────────
INTERDICTIONS CRITIQUES ⛔ (EXEMPLES CONCRETS)
────────────────────────

CES PROMPTS SONT INTERDITS (NE JAMAIS GÉNÉRER) :
❌ "LED display showing 'CRÉDIT AGRICOLE €8.95 (-12.4%)'"
❌ "stock market screen with declining chart"
❌ "digital ticker displaying financial data"
❌ "electronic board showing stock prices"
❌ "the action of the chart decline occupies the upper half"
❌ "graph illustrating stock performance"
❌ "people walking in business attire in the foreground"
❌ "businessmen in sharp focus at ground level"

CES PROMPTS SONT VALIDES (TOUJOURS GÉNÉRER COMME ÇA) :
✅ "corporate headquarters building with official logo on facade"
✅ "low-angle shot of Tesla headquarters, official 'T' logo visible on building"
✅ "Crédit Agricole headquarters exterior, official 'CA' logo on building facade"
✅ "architectural shot of corporate building, logo integrated into building design"
✅ "empty ground-level foreground, distant silhouettes only if necessary"

🚫 INTERDICTIONS ABSOLUES :
- AUCUN écran LED/digital affichant des données (prix, pourcentages, graphiques)
- AUCUN graphique de trading, courbe boursière, infographie
- AUCUN dashboard, tableau de bord, visualisation de données
- AUCUN ticker électronique avec cours d'actions
- AUCUN texte flottant (noms d'entreprises, chiffres, pourcentages)
- AUCUN personnage net au premier plan
- AUCUN élément CGI, illustration, dessin

→ L'image doit montrer UNIQUEMENT un BÂTIMENT réel photographié en contre-plongée

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
- Stunning bright sky with sunset stylized sky colors: purple, orange and magenta tones
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

Inclure explicitement dans le prompt que tu génères (DÉBUT DU PROMPT) :
- "corporate headquarters building exterior"
- "low-angle shot" ou "contre-plongée"
- "camera positioned at ground level pointing upward toward the building"
- "single continuous photograph of the building"
- "official company logo on building facade" (PAS "LED display" ou "digital screen")
- "natural perspective with building and logo in upper third"
- "empty foreground" ou "no people in foreground"
- 8K render
- professional photojournalism style
- natural or high-end studio lighting
- realistic depth of field
- subtle natural sensor grain

ET ces NEGATIVE PROMPTS obligatoires (FIN DU PROMPT - RÉPÉTER 2 FOIS) :
PREMIÈRE FOIS :
- ABSOLUTELY NO LED displays or digital screens
- NO stock market tickers showing prices
- NO electronic boards with financial data  
- NO charts or graphs (no "chart showing decline", no "graph illustrating")
- NO data visualizations of any kind
- NO text overlays with stock prices or percentages
- NO people walking in business attire in foreground
- NO businessmen or businesswomen in sharp focus
- physical building architecture only
- architectural logo signage only
- empty ground-level foreground

DEUXIÈME FOIS (RENFORCEMENT) :
- NO digital screens, NO LED displays, NO stock tickers, NO financial data displays
- NO charts, NO graphs, NO data visualizations, NO electronic boards
- NO "action of chart decline", NO "stock performance visualization"
- NO text, NO numbers, NO percentages, NO stock prices visible
- NO people in foreground (sharp or blurred), NO business attire visible
- physical corporate building only, logo integrated into building facade only
- completely empty foreground preferred
- no watermark, no media logo, no captions, no overlays

────────────────────────
EXEMPLE D'OUTPUT ATTENDU (RÉFÉRENCE CRITIQUE)
────────────────────────

Ultra-realistic editorial PRESS PHOTOGRAPH, 8K render, professional photojournalism style.

⚠️ CRITICAL: This example shows EXACTLY what to generate and what NOT to generate.

SUBJECT (MANDATORY)
Tesla headquarters building as the single central subject.
The image represents the company through their PHYSICAL BUILDING, not through screens or data displays.
Example context: "Tesla announces record quarterly deliveries" → show the Tesla BUILDING, NOT a stock chart.

ACTION & COMPOSITION (MANDATORY)
LOW-ANGLE SHOT (contre-plongée) – camera positioned at ground level, pointing upward toward the BUILDING.
The UPPER THIRD contains: the building facade with the official Tesla logo.
The LOWER THIRD contains: ground pavement, building base, empty foreground.
❌ FORBIDDEN: "The upper third contains a LED screen showing Tesla stock price dropping"
✅ CORRECT: "The upper third shows the Tesla headquarters building with official 'T' logo on the facade"

CRITICAL: This must be ONE single continuous photograph of a BUILDING.
NOT a photograph of people + a screen showing data.
Seamless visual unity from bottom to top, consistent lighting and perspective throughout.
The lower third remains clean, uncluttered, with NO people in sharp focus.

CONTEXT (MANDATORY – PHYSICAL BUILDING ONLY)
Tesla headquarters, Gigafactory, or corporate facility BUILDING.
OBLIGATORY visual identifiers:
- Authentic TESLA logo mounted/displayed on the BUILDING FACADE (physical signage on architecture)
- Modern automotive/technology facility BUILDING architecture
- Professional business environment photographed from EXTERIOR
❌ FORBIDDEN: "LED display showing 'TESLA' and stock chart"
✅ CORRECT: "Tesla 'T' logo integrated into building facade design"

The logo must appear as ARCHITECTURAL BRANDING on the building,
NOT as an electronic display or screen.

PEOPLE (STRICT)
❌ ABSOLUTELY NO people walking in business attire in the foreground
❌ NO businessmen/businesswomen in sharp focus at ground level
❌ NO "people crossing in front of the building"
✅ ONLY: very distant, barely visible silhouettes if absolutely necessary (optional)
✅ PREFERRED: completely empty foreground

ART DIRECTION (MANDATORY)
Sunset stylized sky with dominant purple, orange, and magenta tones.
Stunning sunset backdrop behind the corporate BUILDING (not behind a screen).
Atmosphere premium, stunning, financial and aspirational.
PRESS PHOTO realistic style of a BUILDING (not of a data display).

CRITICAL RESTRICTIONS (MANDATORY – REPEAT IN PROMPT)
❌ DO NOT GENERATE: "LED screen displaying Tesla stock declining"
❌ DO NOT GENERATE: "digital ticker showing 'TESLA -5.2%'"
❌ DO NOT GENERATE: "chart showing stock market performance in upper half"
❌ DO NOT GENERATE: "people in business suits walking in foreground"
✅ GENERATE: "Tesla headquarters building, low-angle shot, official logo on building facade"
✅ GENERATE: "architectural photography of corporate building exterior"
✅ GENERATE: "empty ground-level foreground, building rises toward upper third"

NO digital screens, NO data displays, NO stock tickers, NO graphs, NO charts.
NO people in foreground (sharp or blurred).
ONLY physical building architecture with official logo.

NEGATIVE PROMPTS (CRITICAL - MUST INCLUDE):
NO LED displays, NO digital screens, NO stock market tickers, NO financial data displays,
NO charts, NO graphs, NO data visualizations, NO electronic boards,
NO text overlays, NO percentage numbers, NO stock prices,
NO people walking in foreground, NO businessmen, NO businesswomen,
physical building architecture only, architectural signage only, empty foreground.

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
