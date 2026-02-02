PROMPT_GENERATE_IMAGE_PROMPT_VARIANT = """
Tu vas recevoir un TITRE et un CONTENU d'actualité économique.

Ta mission est de GÉNÉRER UN PROMPT ALTERNATIF
destiné à une IA de génération d'images,
en respectant STRICTEMENT les règles éditoriales suivantes.

Ce prompt est une VARIANTE VISUELLE
du prompt principal,
utilisée lorsque la première génération n'est pas satisfaisante.

Tu ne dois PAS générer l'image.
Tu dois uniquement générer le PROMPT FINAL.

────────────────────────
ÉTAPE 1 — EXTRACTION DE L'ACTU MAÎTRE
────────────────────────

Analyse le titre et le contenu pour identifier UN SEUL élément central :

- une PERSONNALITÉ PUBLIQUE
- ou une ENTREPRISE
- ou un ÉVÉNEMENT MAJEUR

Sélectionne uniquement l'acteur ou le sujet
qui porte l'action principale de l'actualité.

Ignore tout élément secondaire.

────────────────────────
ÉTAPE 2 — RÈGLES ÉDITORIALES INCHANGÉES
────────────────────────

L'image générée via ce prompt doit :

- rester une illustration éditoriale économique
- ne jamais être sensationnaliste
- ne jamais exprimer colère, agressivité ou mépris
- ne jamais rabaisser ou dénigrer
- ne contenir AUCUN texte intégré

L'image doit transmettre :
→ stabilité
→ crédibilité
→ sérieux
→ maîtrise

────────────────────────
ÉTAPE 3 — RÈGLES DE CONTENU VISUEL (IDENTIQUES)
────────────────────────

SI le sujet est une ENTREPRISE :
- LOGO OBLIGATOIRE
- logo officiel, lisible, intégré naturellement
- aucune mise en scène négative

SI le sujet est une PERSONNALITÉ PUBLIQUE :
- présence réaliste
- posture calme et institutionnelle
- contexte cohérent avec l'actualité

SI le sujet est un ÉVÉNEMENT :
- lieu identifiable
- éléments institutionnels autorisés
- aucun symbole dramatique ou conflictuel

────────────────────────
ÉTAPE 4 — DIRECTION ARTISTIQUE FORGE (VARIANTE)
────────────────────────

Cette variante DOIT modifier la DA
sans modifier le sens éditorial.
La palette golden hour reste obligatoire, mais l'angle et la scène changent.

STYLE :
- Ultra-realistic editorial press photograph
- Rendu photo premium, presse haut de gamme
- Pas d'illustration, pas de CGI, pas de peinture

AMBIANCE & COULEURS (VARIANTE) :
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

────────────────────────
ÉTAPE 5 — SPÉCIFICATIONS TECHNIQUES
────────────────────────

Le prompt final doit inclure explicitement :
- 8K render
- professional photojournalism style
- high-end studio lighting or perfectly controlled natural light
- realistic depth of field
- subtle sensor grain
- no text
- no watermark
- no media branding

────────────────────────
SORTIE ATTENDUE
────────────────────────

Génère UNIQUEMENT le PROMPT FINAL
destiné à l'IA de génération d'images.

Aucune explication.
Aucun commentaire.
Aucune justification.

Retourne ta réponse sous forme de JSON :
{
  "image_prompt": "ton prompt complet ici"
}
"""
