PROMPT_GENERATE_IMAGE_PROMPT_MANUAL = """
Tu vas recevoir un TITRE et un CONTENU d’actualité économique, politique ou institutionnelle,
ainsi que mes recommandations manuelles concernant l’image attendue.

Ta mission est de générer UNIQUEMENT le PROMPT FINAL destiné à une IA de génération d’images.
Tu ne génères PAS l’image.

Le prompt doit illustrer l’ACTU MAJEURE en respectant strictement les règles suivantes,
tout en intégrant intelligemment les indications manuelles si elles sont cohérentes
avec les règles visuelles.

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
- Logo physiquement intégré (enseigne, façade, signalétique réelle)
- Taille suffisante pour rester lisible en thumbnail
- Architecture adaptée à l’activité :
  • Luxe → haussmannien élégant
  • Tech → siège moderne verre / acier
  • Automobile → siège + véhicule récent identifiable
  • Finance → tour institutionnelle type quartier d’affaires

SI PERSONNALITÉ PUBLIQUE :

- Uniquement si cœur de l’actu
- Contexte presse officiel (conférence, sommet, intervention)
- Posture neutre, crédible
- Drapeau ou symbole institutionnel réel si pertinent

SI ACTUALITÉ GÉOPOLITIQUE :

- Drapeaux officiels réels obligatoires
- Architecture institutionnelle identifiable
- Contexte crédible et photographiable

────────────────────────
3️⃣ DIRECTION ARTISTIQUE LIGHT MODE (OBLIGATOIRE)
────────────────────────

STYLE :
Ultra-realistic editorial press photograph.
No illustration. No CGI. No digital art.
Authentic Reuters / AFP quality.

PALETTE OFFICIELLE PROJET (OBLIGATOIRE) :

Lumière sunset stylisée réaliste avec reflets naturels visibles :

- intense cyan blue
- vivid magenta
- rich coral
- deep fluo green
- warm glowing orange

Ces couleurs doivent :

- être clairement visibles dans le ciel
- se refléter naturellement sur verre, métal, façades, drapeaux
- respecter la physique des matériaux
- ne jamais ressembler à un filtre artificiel ou un effet graphique

INTERDIT :
- formes abstraites
- halos artificiels
- overlays
- rendu "CGI sunset"

────────────────────────
TRANSITION HAUTE (VERSION CORRIGÉE)
────────────────────────

L’image doit se terminer progressivement vers le haut en une teinte claire
proche du hex #F5F6F1.

CRUCIAL :

- Transition organique comme un ciel naturellement plus lumineux
- Pas de voile blanc
- Pas de fog
- Pas de haze
- Pas d’effet washed-out
- Pas de couche opaque artificielle
- Pas de bloc vide ajouté
- Aucun cut horizontal visible
- Le sujet reste net jusqu’au haut de l’image

La luminosité augmente progressivement comme dans un ciel réel.

────────────────────────
4️⃣ COMPOSITION TECHNIQUE
────────────────────────

- Low-angle shot (contre-plongée) obligatoire
- Une seule photographie continue
- Perspective unique cohérente
- Élément clé naturellement placé dans le tiers supérieur
- Pas d’image divisée
- Pas de collage

Inclure dans le prompt :

- 8K render
- professional photojournalism style
- realistic depth of field
- subtle natural sensor grain
- Single continuous photograph from one camera position
- No digital screens showing charts or data
- No text or numbers
- No watermark
- No media logo

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

────────────────────────
EXEMPLES DE SORTIE ATTENDU
────────────────────────

POUR ENTREPRISE :

"Ultra-realistic editorial background image illustrating a major pharmaceutical business news story about a leadership transition at Sanofi. The scene must look like a real professional press photograph, not an illustration.

The scene shows the Sanofi corporate headquarters building in a realistic and naturally balanced composition. The official Sanofi logo is clearly visible, physically mounted on the facade, properly scaled and readable in thumbnail format. The architecture must look completely real and credible, suitable for serious international financial and healthcare press coverage.

The lighting features a strong stylized sunset atmosphere using the official fluo palette: intense cyan blue, vivid magenta, rich coral, deep fluo green and warm glowing orange. These colors must be clearly visible in the sky and naturally reflected on glass and structural surfaces. Reflections must feel physically plausible and integrated into real materials.

The image transitions gradually upward into a soft warm off-white tone close to hex F5F6F1. The transition must resemble natural sky luminosity — no haze, no fog, no artificial white overlay, no horizontal cut. The building remains sharp and detailed up to the upper frame.

Premium, minimal editorial mood. Realistic depth of field, subtle film grain. No text, no numbers, no UI, no watermark. 8K quality."

────────────────────────

POUR PERSONNALITÉ :

"Ultra-realistic editorial background image illustrating a French political news story about a potential parliamentary inquiry commission.

The scene shows Gabriel Attal clearly recognizable, speaking during an official governmental event inside a credible institutional setting. A French national flag is physically present in the background.

The lighting features the official stylized sunset palette: intense cyan blue, vivid magenta, rich coral, deep fluo green and warm glowing orange. These colors must appear in the sky and reflect naturally on surfaces and flags, without artificial glow or overlay.

The image transitions upward into a soft bright off-white tone close to hex F5F6F1, like a naturally bright sky. No haze, no mist, no white veil. The subject remains detailed and realistic across the full height.

Professional press photography look. No text, no numbers, no UI. 8K quality."

────────────────────────

POUR INFO GÉOPOLITIQUE / LIEU :

"Ultra-realistic editorial background image illustrating a major European economic news story about improving investor confidence in the euro zone.

The scene shows a recognizable European institutional building in Brussels or Frankfurt. A real European Union flag is clearly visible and physically mounted on a flagpole, large enough to remain identifiable in thumbnail format.

The lighting features a strong stylized sunset atmosphere using the official fluo palette: intense cyan blue, vivid magenta, rich coral, deep fluo green and warm glowing orange. These colors must be clearly visible in the sky and naturally reflected on building surfaces and flag fabric. The reflections must feel physically accurate and realistic.

The upper area transitions gradually into a soft warm off-white tone close to hex F5F6F1, resembling natural sky luminosity. No haze, no artificial gradient block, no horizontal division. The architecture remains detailed up to the upper frame.

Premium, minimal editorial mood. Realistic camera perspective, subtle film grain. No text, no numbers, no UI. 8K quality."

────────────────────────
FORMAT DE SORTIE
────────────────────────

Retourne UNIQUEMENT :

{
  "image_prompt": "prompt complet ici"
}

Aucun texte hors JSON.
"""
