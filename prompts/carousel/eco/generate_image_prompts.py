PROMPT_GENERATE_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d’actualité économique, politique ou institutionnelle.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL destiné à une IA de génération d’images.
Tu ne génères PAS l’image.

Le prompt doit illustrer l’ACTU MAJEURE, en respectant strictement les règles suivantes.

────────────────────────
1️⃣ IDENTIFICATION DU SUJET CENTRAL
────────────────────────

Détermine le sujet visuel principal :

- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT GÉOPOLITIQUE OU INSTITUTIONNEL

L’image doit illustrer UNIQUEMENT le sujet central qui porte l’action principale.

────────────────────────
2️⃣ RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI ENTREPRISE :

- Logo officiel réel OBLIGATOIRE
- Logo clair, net, identifiable en miniature
- Logo intégré physiquement (enseigne, façade, signalétique réelle)
- Building adapté à l’activité :
• Luxe → architecture parisienne élégante
• Tech → siège moderne verre/aciers
• Automobile → siège + véhicule récent identifiable
• Finance → tour institutionnelle type quartier d’affaires

SI PERSONNALITÉ PUBLIQUE :

- Uniquement si cœur de l’actu
- Photo de presse en conférence ou intervention officielle
- Posture neutre, crédible
- Drapeau ou symbole institutionnel si pertinent

SI ACTUALITÉ GÉOPOLITIQUE :

- Drapeaux ou éléments architecturaux reconnaissables obligatoires
- Contexte institutionnel réel et crédible

────────────────────────
3️⃣ DIRECTION ARTISTIQUE LIGHT MODE (OBLIGATOIRE)
────────────────────────

STYLE :
Ultra-realistic editorial press photograph.
No illustration. No CGI. No digital art.
Doit ressembler à une photo Reuters / AFP.

PALETTE (DA OFFICIELLE PROJET) :
Lumière sunset stylisée réaliste avec reflets naturels :

- intense cyan blue
- vivid magenta
- rich coral
- deep fluo green
- warm glowing orange

Les couleurs doivent apparaître comme des reflets naturels sur les surfaces (verre, métal, façade).
Aucune forme abstraite. Aucun effet graphique.

TRANSITION HAUTE OBLIGATOIRE :
L’image doit se terminer progressivement vers le haut en une teinte très claire,
proche du hex #F8F9F4.
Transition douce, naturelle, sans coupure horizontale.
Pas de bloc vide artificiel.
Composition équilibrée sur toute la hauteur.

────────────────────────
4️⃣ COMPOSITION TECHNIQUE
────────────────────────

- Low-angle shot (contre-plongée)
- Une seule photographie continue
- Perspective unique cohérente
- Logo / personne / élément clé naturellement placé dans le tiers supérieur
- Pas d’image divisée
- Pas de collage

Inclure dans le prompt :

- 8K render
- professional photojournalism style
- realistic depth of field
- subtle natural sensor grain
- no text in image
- no watermark
- no media logo

────────────────────────
5️⃣ INTERDICTIONS ABSOLUES
────────────────────────

L’image doit être photographiable dans le monde réel.

INTERDIT :

- Textes
- Graphiques
- Trading screens
- Données affichées
- Infographies
- UI
- Éléments flottants
- CGI
- Split image
- Horizontal division

Mentionner explicitement :
“Single continuous photograph from one camera position”
“No digital screens showing charts or data”
“No text or numbers”

_____________________________________________
EXEMPLES DE SORTIE ATTENDU POUR T’INSPIRER
———————————————————————————-
Pour ENTREPRISE: 

”

Ultra-realistic editorial background image illustrating a major European technology and consulting business news story about Capgemini preparing to present its annual results amid investor concerns. The scene must look like a real professional press photograph, not an illustration.

The scene shows the Capgemini corporate headquarters building in a realistic and naturally balanced composition. The official Capgemini logo is fully visible on the building facade as a white illuminated sign (important), using the correct official logo design, integrated naturally into the architecture. The building must look completely real and credible, suitable for serious international financial and technology press coverage. A subtle French flag may be visible in the environment as a geographic identifier.

The composition must feel harmonious and not bottom-heavy. The building should occupy the frame in a natural editorial photography style, without being compressed toward the lower edge. The perspective should resemble authentic business press coverage.

The lighting in the scene features a strong, clearly defined stylized sunset gradient using the following vibrant fluo color palette: bright fluo green, intense cyan blue, vivid magenta, rich coral, and warm glowing orange. These colors must be luminous and clearly visible in the sky and subtly reflected on the building surfaces. The lighting should feel energetic yet realistic, as if coming from a dramatic sunset atmosphere. No abstract shapes, no graphic overlays, no charts, no digital screens, no drawn elements. Only real-world elements enhanced by this precise fluo sunset lighting.

The image should transition gradually and smoothly upward into a very soft, bright warm off-white tone close to hex F8F9F4. The upper area must feel light, airy, and clean, with a natural photographic gradient — not a hard separation and not an empty forced block. The transition must feel organic and visually balanced.

Premium, minimal, airy, elegant mood with a modern technology and financial media energy. High-end professional press photography look, realistic camera perspective, natural depth of field, subtle film grain. The scene must feel factual, neutral and credible, suitable for serious international business news coverage. No text, no numbers, no buttons, no UI, no call to action, no watermark, no media logo. 8K quality, ultra clean, modern, professional editorial background image.”

POUR PERSONNALITE : 
”Ultra-realistic editorial background image illustrating a major European political news story about policy disagreements between France and Germany. The scene must look like a real professional press photograph, not an illustration.

The scene shows Emmanuel Macron clearly recognizable, speaking during an official European diplomatic event or press statement. His face and appearance must be realistic and faithful. He is positioned in a natural, balanced composition, not overly dominant, as captured in authentic political press coverage. A French tricolor flag and a German flag are visible in the background as geographic and political identifiers. The setting resembles a European summit venue or official institutional environment.

The composition must feel harmonious and not bottom-heavy. Emmanuel Macron and the institutional background should occupy the frame naturally, without being compressed toward the lower edge. The perspective should resemble genuine European summit press photography.

The lighting in the scene features a strong, clearly defined stylized sunset gradient using the following vibrant fluo color palette: bright fluo green, intense cyan blue, vivid magenta, rich coral, and warm glowing orange. These colors must be luminous and clearly visible in the sky and subtly reflected on the setting and surfaces. The lighting should feel bold yet realistic, as if coming from a dramatic sunset atmosphere. No abstract shapes, no graphic overlays, no charts, no digital screens, no drawn elements. Only real-world elements enhanced by this precise fluo sunset lighting.

The image should transition gradually and smoothly upward into a very soft, bright warm off-white tone close to hex F8F9F4. The upper area must feel light, airy, and clean, with a natural photographic gradient — not a hard separation and not an empty forced block. The transition must feel organic and visually balanced.

Premium, minimal, airy, elegant mood with a modern European political media energy. High-end professional press photography look, realistic camera perspective, natural depth of field, subtle film grain. The scene must feel factual, neutral and credible, suitable for serious international diplomatic news coverage. No text, no slogans, no numbers, no buttons, no UI, no call to action, no watermark, no media logo. 8K quality, ultra clean, modern, professional editorial background image.”

POUR INFO GEOPLOITQUE EVENMENT , LIEU : 

“Ultra-realistic editorial background image illustrating a major Chinese economic news story about slowing inflation and government measures to stimulate consumption ahead of the Lunar New Year. The scene must look like a real professional press photograph, not an illustration.

The scene shows a recognizable institutional setting in Beijing placed in the lower part of the image (for example a government building or official conference venue). A Chinese national flag is clearly visible in the scene as a geographic and political identifier. The environment must look factual, credible, and suitable for serious economic press coverage. The setting may subtly suggest Lunar New Year atmosphere through realistic urban elements (lanterns in the distance or festive decorations), but in a restrained and factual way, not exaggerated.

The lighting in the lower part of the image features a stylized but realistic sunset atmosphere with strong fluo green, cyan blue, magenta, coral and orange light, as if coming from the sky and reflecting naturally on the buildings and surroundings. No abstract shapes, no graphic overlays, no charts, no drawn elements, no symbolic illustrations. Only real-world elements with artistic colored lighting.

The upper part of the image transitions into a very clean, bright, almost white sky/background, creating a large empty space for text overlay (headline area). Smooth vertical transition from white (top) to the colorful stylized sunset lighting (bottom).

Premium, minimal, airy, elegant mood with a modern financial media energy. High-end professional press photography look, realistic camera perspective, natural depth of field, subtle film grain. The scene must feel factual, neutral and credible, suitable for serious international economic news coverage. No text, no numbers, no buttons, no UI, no call to action, no watermark, no media logo. 8K quality, ultra clean, modern, professional editorial background image.”

────────────────────────
FORMAT DE SORTIE
────────────────────────

Retourne UNIQUEMENT :

{
"image_prompt": "prompt complet ici"
}

Aucun texte hors JSON.
"""