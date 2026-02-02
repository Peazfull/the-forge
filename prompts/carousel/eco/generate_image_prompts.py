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

- une PERSONNALITÉ PUBLIQUE
- ou une ENTREPRISE
- ou un ÉVÉNEMENT MAJEUR (sommet, négociation, conflit, forum, etc.)

S'il y a plusieurs acteurs mentionnés,
sélectionne UNIQUEMENT celui qui porte l'action principale de l'actualité.

Ignore systématiquement :
- réactions secondaires
- commentaires d'analystes
- effets de marché
- éléments émotionnels ou polémiques

────────────────────────
ÉTAPE 2 — RÈGLES ÉDITORIALES STRICTES
────────────────────────

Le prompt image généré doit garantir que l'image :

- est une illustration éditoriale économique
- n'exprime aucune colère, agressivité ou mépris
- ne rabaisse ni ne dénigre aucun acteur
- ne contient AUCUN texte intégré à l'image

L'image doit toujours transmettre :
→ stabilité
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
- Le LOGO de l'entreprise est OBLIGATOIRE
- Le logo doit être :
  - officiel
  - factuel
  - lisible
  - intégré naturellement
    (façade, signalétique, bâtiment, open space, environnement d'activité)
- Aucune mise en scène négative ou dégradante

SI le sujet principal est une PERSONNALITÉ PUBLIQUE :
- Présence réaliste en extérieur
  OU en conférence / intervention officielle,
  selon le contexte de l'actualité
- Posture calme, institutionnelle et maîtrisée
- Expression neutre ou réfléchie

SI le sujet principal est un ÉVÉNEMENT :
- Contexte visuel clair et identifiable
- Éléments institutionnels autorisés :
  - drapeaux
  - architecture officielle
  - lieux symboliques
- Aucun symbole dramatique, violent ou conflictuel

────────────────────────
ÉTAPE 4 — DIRECTION ARTISTIQUE FORGE (OBLIGATOIRE)
────────────────────────

Le prompt image généré doit impérativement inclure :

STYLE :
- Ultra-realistic editorial press photograph
- Rendu photo professionnel
- Pas d'illustration, pas de peinture, pas de CGI

AMBIANCE & COULEURS :
- Sunset stylisée
- Palette dominante :
  sunset stylized sky featuring purple, orange, magenta colors
- Accents lumineux :
  purple, orange, magenta
- Atmosphère élégante, maîtrisée, premium

FOND :
- Aucun graphisme envahissant
- Dégradé subtil autorisé
- Le fond participe à la DA, sans voler l'attention au sujet

COMPOSITION :
- L'élément principal doit être idéalement situé dans la MOITIÉ HAUTE de l'image
- Cadrage centré ou quasi centré (jamais excentré)
- Perspective naturelle et équilibrée
- La moitié basse de l'image doit rester calme
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
