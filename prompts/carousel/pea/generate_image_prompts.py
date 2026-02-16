PROMPT_GENERATE_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité économique, politique ou institutionnelle.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL destiné à une IA de génération d'images.
Tu ne génères PAS l'image.

Le prompt doit illustrer l'ACTU MAJEURE, en respectant strictement les règles suivantes.

────────────────────────
1️⃣ IDENTIFICATION DU SUJET CENTRAL
────────────────────────

Détermine le sujet visuel principal :

- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT GÉOPOLITIQUE OU INSTITUTIONNEL

L'image doit illustrer UNIQUEMENT le sujet central qui porte l'action principale.

────────────────────────
2️⃣ RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI ENTREPRISE :

- Logo officiel réel OBLIGATOIRE
- Logo clair, net, identifiable en miniature
- Logo intégré physiquement (enseigne, façade, signalétique réelle)
- Building adapté à l'activité :
  • Luxe → architecture parisienne élégante
  • Tech → siège moderne verre/aciers
  • Automobile → siège + véhicule récent identifiable devant
  • Finance → tour institutionnelle type quartier d'affaires
  • etc... soit intelligent là dessus 


SI PERSONNALITÉ PUBLIQUE :

- Uniquement si cœur de l'actu
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

Les couleurs doivent apparaître comme des reflets naturels sur les surfaces (verre, métal, façade, drapeaux).
Aucune forme abstraite. Aucun effet graphique.

TRANSITION HAUTE OBLIGATOIRE (VERSION CORRIGÉE) :

L'image doit se terminer progressivement vers le haut en une teinte très claire,
proche du hex #F8F9F4.

IMPORTANT :

- La transition doit ressembler à un ciel naturellement plus lumineux
- Pas de voile blanc
- Pas de haze
- Pas de mist
- Pas de fog
- Pas d'effet washed-out
- Pas de couche opaque artificielle
- Aucun bloc vide ajouté

Le sujet principal (bâtiment, drapeau, personnalité) doit rester net et détaillé jusqu'en haut de l'image.

────────────────────────
4️⃣ COMPOSITION TECHNIQUE
────────────────────────

- Low-angle shot (contre-plongée)
- Une seule photographie continue
- Perspective unique cohérente
- Logo / personne / élément clé naturellement placé dans le tiers supérieur
- Pas d'image divisée
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

L'image doit être photographiable dans le monde réel.

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
"Single continuous photograph from one camera position"
"No digital screens showing charts or data"
"No text or numbers"

_____________________________________________
EXEMPLES DE SORTIE ATTENDU POUR T'INSPIRER
_____________________________________________

POUR ENTREPRISE:

Ultra-realistic editorial background image illustrating a major European technology and consulting business news story about Capgemini preparing to present its annual results amid investor concerns. The scene must look like a real professional press photograph, not an illustration.

The scene shows the Capgemini corporate headquarters building in a realistic and naturally balanced composition. The official Capgemini logo is fully visible on the building facade as a white illuminated sign (important), using the correct official logo design, integrated naturally into the architecture. The building must look completely real and credible, suitable for serious international financial and technology press coverage.

The lighting in the scene features a strong, clearly defined stylized sunset atmosphere using the official project fluo palette: intense cyan blue, vivid magenta, rich coral, deep fluo green, and warm glowing orange. These colors must be clearly visible in the sky and naturally reflected on the building surfaces. The reflections must feel physically plausible and integrated into real materials, not artificial.

The image should transition gradually and smoothly upward into a very soft, bright warm off-white tone close to hex F8F9F4. The transition must resemble a natural brightening of the sky, without haze, without fog, without white overlay, and without any horizontal cut. The upper area must remain detailed and photographically realistic.

Premium, minimal, airy, elegant mood with modern financial media energy. Realistic camera perspective, natural depth of field, subtle film grain. No text, no numbers, no UI, no watermark, no media logo. 8K quality.

────────────────────────

POUR PERSONNALITÉ:

Ultra-realistic editorial background image illustrating a major European political news story about policy disagreements between France and Germany. The scene must look like a real professional press photograph.

The scene shows Emmanuel Macron clearly recognizable, speaking during an official European diplomatic event. A French flag and a German flag are visible as real physical flags.

The lighting features a strong stylized sunset using the official fluo palette: intense cyan blue, vivid magenta, rich coral, deep fluo green, and warm glowing orange, naturally reflected on surfaces and surroundings.

The image must transition gradually and smoothly upward into a very soft bright off-white tone close to hex F8F9F4. The transition must feel like natural sky luminosity increasing — no haze, no fog, no white overlay, no horizontal division. The subject must remain sharp and detailed up to the upper frame.

Professional press photography look. No text, no numbers, no UI, no watermark. 8K quality.

────────────────────────

POUR INFO GÉOPOLITIQUE / LIEU:

Ultra-realistic editorial background image illustrating a major geopolitical economic news story in Beijing.

The scene shows a recognizable institutional setting in Beijing placed in the lower part of the image. A Chinese national flag is clearly visible and physically present. The architecture must be credible and institutional.

The lighting in the lower part of the image features a strong, clearly defined stylized sunset atmosphere using the official project fluo palette: intense cyan blue, vivid magenta, rich coral, deep fluo green, and warm glowing orange. These colors must be visible in the sky and naturally reflected on the building, windows, flag and surrounding surfaces. Reflections must feel physically plausible, not graphic.

The upper part must transition gradually and smoothly into a very soft bright off-white tone close to hex F8F9F4. The transition must be organic and seamless, resembling natural sky brightness increasing — not haze, not mist, not fog, not a white overlay, and not a hard horizontal cut. The building and flag must remain sharp and detailed up to the upper area.

Premium, minimal, airy editorial mood. Realistic depth of field, subtle film grain. No text, no numbers, no UI, no watermark. 8K quality.

────────────────────────
FORMAT DE SORTIE
────────────────────────

Retourne UNIQUEMENT :

{
"image_prompt": "prompt complet ici"
}

Aucun texte hors JSON.
"""
