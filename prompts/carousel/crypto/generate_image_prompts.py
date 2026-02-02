PROMPT_GENERATE_IMAGE_PROMPT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité économique.

Ta mission est de GÉNÉRER LE PROMPT FINAL
qui servira à générer l'image illustrant cette actualité.

Tu ne dois PAS générer l'image.
Tu dois uniquement générer le PROMPT destiné à une IA de génération d'images.

Le prompt final doit être directement exploitable
et respecter strictement les règles éditoriales et artistiques suivantes.

────────────────────────
ÉTAPE 1 — EXTRACTION DE L'ACTU MAÎTRE
────────────────────────

Analyse le titre et le contenu pour identifier UN SEUL élément central,
obligatoirement unique :

- ou une ENTREPRISE
- ou un ÉVÉNEMENT MAJEUR (sommet, négociation, conflit, forum, etc.)

S'il y a plusieurs éléments mentionnés,
sélectionne UNIQUEMENT celui qui porte l'action principale de l'actualité.


────────────────────────
ÉTAPE 2 — RÈGLES ÉDITORIALES STRICTES
────────────────────────

Le prompt image généré doit garantir que l'image :

- est une illustration éditoriale économique
- n'exprime aucune colère, agressivité ou mépris
- ne rabaisse ni ne dénigre aucun acteur
- ne contient AUCUN texte intégré à l'image

L'image doit toujours transmettre :
→ crédibilité
→ lisibilité
→ sérieux éditorial

La tension, la critique ou la dureté de l'actualité
doivent être portées uniquement par le TEXTE,
jamais par l'image.

────────────────────────
ÉTAPE 3 — RÈGLES DE CONTENU VISUEL (OBLIGATOIRES)
────────────────────────

SI le sujet principal est une ENTREPRISE :
- Le LOGO officiel de l'entreprise est OBLIGATOIRE
- Le logo doit être :
  - officiel
  - factuel
  - lisible
  - intégré naturellement
    (façade, signalétique, bâtiment, open space, environnement d'activité)
- La composition de l'action principale doit être centrée sur la moitié haute de l'image
- Le logo doit être intégré de façon réaliste et discrète (taille d'enseigne crédible)
- Aucune mise en scène négative ou dégradante

SI le sujet principal est une PERSONNALITÉ PUBLIQUE très connues :
- Présence réaliste en extérieur
  OU en conférence / intervention officielle,
  selon le contexte de l'actualité
- Avec logo officiel de la société ou de l'évènement

SI le sujet principal est un ÉVÉNEMENT :
- Contexte visuel clair et identifiable
- Éléments institutionnels autorisés :
  - drapeaux
  - architecture officielle
  - lieux symboliques
- Aucun symbole dramatique, violent ou conflictuel

────────────────────────
ÉTAPE 4 — DIRECTION ARTISTIQUE (OBLIGATOIRE)
────────────────────────

Le prompt image généré doit impérativement inclure :

STYLE :
- Ultra-realistic editorial press photograph
- Rendu photo professionnel
- Pas d'illustration, pas de peinture, pas de CGI

AMBIANCE & COULEURS :
- Sunset golden hour uniquement
- Couleurs dominantes :
  golden amber, warm orange, soft sand tones
- Accents secondaires :
  subtle magenta, violet
- Dégradés lisses, pas de contrastes durs
- Atmosphère premium, chaleureuse, élégante

FOND :
- Aucun graphisme envahissant
- Dégradé subtil autorisé
- Le fond participe à la DA, sans voler l'attention au sujet

COMPOSITION :
- Tous les éléments essentiels (logo + contexte principal)
  doivent être dans la MOITIÉ HAUTE de l'image
- Cadrage centré ou quasi centré (jamais excentré)
- Perspective naturelle et équilibrée
- La moitié basse de l'image doit rester calme, minimaliste, dégagée
  pour accueillir un titre ajouté manuellement
- Aucun texte généré dans l'image

────────────────────────
ÉTAPE 5 — SPÉCIFICATIONS TECHNIQUES
────────────────────────

Le prompt final doit contenir explicitement :
- 8K render
- style photojournalisme professionnel
- éclairage studio haut de gamme
  ou lumière naturelle parfaitement maîtrisée
- profondeur de champ réaliste
- grain capteur léger et naturel
- aucun texte dans l'image
- aucun watermark
- aucun logo média

IMPORTANT (CRYPTO / ENTREPRISE) :
- La sortie doit suivre explicitement cette structure (adaptée à l'actu) :
"Ultra-realistic editorial press photograph, 8K render. A symbolic representation of a global decentralized blockchain network, treated as a serious and strategic digital infrastructure. The official [ACTEUR PRINCIPAL] logo visible, accurate and readable, integrated in a factual and institutional way. COLOR CODES (MANDATORY): Dominant colors: golden amber, warm orange, soft sand tones. Secondary accents: subtle magenta and violet. Sunset golden hour atmosphere only. Smooth gradients, no harsh contrasts. Premium, warm, elegant lighting. COMPOSITION (MANDATORY): All essential visual elements (logo + main context) MUST be positioned in the UPPER HALF of the image. Framing centered or near-centered (never excentré). Natural and balanced perspective. LOWER HALF of the image must remain calm, minimal and uncluttered to allow manual headline overlay. No text generated inside the image. STYLE & TONE: Professional photojournalism realism. No illustration style, no CGI look, no painting. No charts, no numbers, no hype visuals. No dramatic, aggressive or emotional cues. Mood: stability, credibility, long-term strength. TECHNICAL: Natural light simulation, realistic depth of field, subtle sensor grain, no watermark, no media branding, no text."

────────────────────────
SORTIE ATTENDUE
────────────────────────

Génère UNIQUEMENT le PROMPT FINAL
destiné à une IA de génération d'images.

Le prompt doit être :
- clair
- structuré
- précis
- directement exploitable
- sans explication, sans justification, sans commentaire autour

Retourne ta réponse sous forme de JSON :
{
  "image_prompt": "ton prompt complet ici"
}
"""
