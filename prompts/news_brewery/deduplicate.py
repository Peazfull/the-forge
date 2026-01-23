PROMPT_DEDUPLICATE = """
MISSION
Tu reçois une liste de sujets d'actualité structurés (Titre + Paragraphe).
Tu dois identifier et fusionner les doublons en un seul article consolidé.

QU'EST-CE QU'UN DOUBLON ?
Deux sujets sont des doublons SI :
- Ils parlent de la MÊME entreprise/acteur (ex: Alstom, LVMH, etc.)
- ET ils concernent le MÊME événement/annonce (ex: inauguration, résultats, acquisition)
- Même si les titres sont formulés différemment

EXEMPLES DE DOUBLONS À FUSIONNER :
✓ "Alstom inaugure un centre" + "Alstom ouvre une usine" → Si même centre/usine = DOUBLON
✓ "Apple annonce ses résultats" + "Résultats trimestriels d'Apple" → DOUBLON
✓ "LVMH acquiert une marque" + "LVMH finalise son acquisition" → DOUBLON

EXEMPLES QUI NE SONT PAS DES DOUBLONS :
✗ "Alstom inaugure un centre" + "Alstom annonce des licenciements" → 2 événements différents
✗ "Apple publie iOS 18" + "Apple lance un nouveau iPhone" → 2 annonces distinctes
✗ "Total en France" + "Total au Brésil" → Même entreprise mais contextes géographiques distincts

CE QUE TU DOIS FAIRE
1. IDENTIFIER les doublons selon les critères ci-dessus
2. FUSIONNER les doublons en un seul article :
   - Prendre le titre le plus précis et informatif
   - Consolider le contenu en combinant toutes les informations uniques
   - Ne perdre AUCUNE information factuelle (chiffres, dates, noms, contexte)
3. CONSERVER tels quels les sujets uniques (pas de doublons)
4. Ne PAS reformuler ni modifier le style des textes conservés

ALGORITHME DE FUSION
Pour chaque doublon détecté :
1. Choisir le meilleur titre (le plus informatif)
2. Fusionner les paragraphes en un seul :
   - Commencer par le contexte général
   - Ajouter tous les détails uniques de chaque version
   - Éliminer les répétitions
   - Conserver chronologie et logique
3. Vérifier qu'aucun chiffre, date ou nom n'est perdu

RÈGLES STRICTES
- Ne PAS inventer d'informations
- Ne PAS ajouter d'analyse ou d'opinion
- Ne PAS reformuler les parties non-dupliquées
- Être AGRESSIF sur la détection : en cas de doute, c'est probablement un doublon
- Sortie en texte brut uniquement, sans JSON, sans markdown, sans numérotation

FORMAT DE SORTIE (EXACT)
Titre du sujet 1
Paragraphe détaillé du sujet 1 avec toutes les informations consolidées.

Titre du sujet 2
Paragraphe détaillé du sujet 2.

Titre du sujet 3
Paragraphe détaillé du sujet 3.

EXEMPLE CONCRET
INPUT :
Alstom inaugure améliore ses résultats grace a une politique de formation.
Alstom a inauguré un nouveau centre de formation dédié au soudage à Mâtranovák en Hongrie.

Alstom ouvre un nouveau centre
Le groupe Alstom a procédé à l'ouverture d'un centre de formation à Mâtranovák. Carine Siegwalt souligne l'importance.

Tesla annonce x2 de ses ventes de véhicules électriques aux Etats-Unis.
Tesla a publié des résultats trimestriels records avec un chiffre d'affaires de 25 milliards.

OUTPUT :
Alstom améliore ses résultats grace a une politique de formation.
En enffet, Alstom a inauguré un nouveau centre de formation dédié au soudage et au montage à Mâtranovák en Hongrie. Carine Siegwalt, directrice générale de l'usine, a souligné l'importance d'attirer des professionnels bien formés pour garantir la qualité et la sécurité des produits.

Tesla annonce x2 de ses ventes de véhicules électriques aux Etats-Unis.
Des résultats records publiés avec un chiffre d'affaires de 25 milliards.
"""
