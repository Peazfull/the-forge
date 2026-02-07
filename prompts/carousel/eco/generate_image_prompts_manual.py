PROMPT_GENERATE_IMAGE_PROMPT_MANUAL= """
Tu vas recevoir un TITRE et un CONTENU d’actualité économique, politique ou institutionnelle avec mes recommandations manuelles de l'image attendu en plus. 

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

Sélectionne UN SEUL SUJET VISUEL CENTRAL :
- ENTREPRISE
- PERSONNALITÉ PUBLIQUE
- LIEU / ÉVÉNEMENT ÉCONOMIQUE OU INSTITUTIONNEL

L’image doit illustrer :
→ l’acteur ou le lieu qui porte l’action principale
→ jamais les réactions, conséquences ou commentaires secondaires

────────────────────────
RÈGLE VISUELLE MAJEURE (NON NÉGOCIABLE)
────────────────────────

L’ACTION VISUELLE PRINCIPALE
DOIT OBLIGATOIREMENT ÊTRE SITUÉE
DANS LA MOITIÉ HAUTE DE L’IMAGE.

La MOITIÉ BASSE doit rester calme,
propre,
sans élément fort,
prévue pour accueillir du texte ajouté manuellement.

Aucun personnage secondaire visible.
Autorisé uniquement :
- silhouettes très lointaines et discrètes.

────────────────────────
RÈGLES STRICTES PAR TYPE DE SUJET
────────────────────────

SI LE SUJET EST UNE ENTREPRISE :
- LE LOGO OFFICIEL EST OBLIGATOIRE
- Image INVALIDE sans logo officiel visible
- Logo authentique, lisible, intégré naturellement
- Contexte : façade, siège, environnement professionnel réel

SI LE SUJET EST UNE PERSONNALITÉ PUBLIQUE :
- Uniquement personnalité publique connue
- Contexte OBLIGATOIRE :
  conférence officielle, intervention publique ou déplacement institutionnel
- Posture calme, neutre, maîtrisée

SI LE SUJET EST UN LIEU / ÉVÉNEMENT :
- Éléments de reconnaissance OBLIGATOIRES :
  drapeaux, signalétique officielle, monument, architecture identifiable
- Contexte institutionnel clair et crédible

────────────────────────
DIRECTION ARTISTIQUE (OBLIGATOIRE)
────────────────────────

STYLE :
- Ultra-realistic editorial press photograph
- Photojournalisme économique
- Aucun style illustratif, artistique ou CGI

PALETTE COULEURS OBLIGATOIRE :
- Sunset stylized sky
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
- no watermark
- no media logo
- no captions
- no overlays

────────────────────────
EXEMPLE D’OUTPUT ATTENDU (RÉFÉRENCE)
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
Sunset stylized sky with dominant purple, orange, and magenta tones.
Subtle, elegant light accents.
Atmosphere premium, calm, credible, institutional.

TECHNICAL REQUIREMENTS (MANDATORY)
Natural or high-end studio lighting.
Realistic depth of field.
Subtle natural sensor grain.
No text in image.
No watermark.
No media logo.
No captions or overlays.

────────────────────────
FORMAT DE SORTIE (OBLIGATOIRE)
────────────────────────

Retourne ta réponse UNIQUEMENT sous forme de JSON valide :

{
  "image_prompt": "ton prompt complet ici"
}

Aucun texte en dehors du JSON.
"""
