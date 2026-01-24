PROMPT_DEDUPLICATE = """
MISSION
Tu reçois une liste de sujets d'actualité structurés (Titre + Paragraphe).
Tu dois identifier et fusionner les doublons en un seul article consolidé, avec la même qualité qu'un article unique.

⚠️ IMPÉRATIF ANTI-PLAGIAT ⚠️
Lors de la fusion, tu DOIS reformuler pour éviter tout plagiat :
- CHANGER les mots et expressions (synonymes, tournures différentes)
- VARIER la structure des phrases
- CONSERVER strictement tous les chiffres, dates, noms, faits

QU'EST-CE QU'UN DOUBLON ?
Deux sujets sont des doublons SI :
- Ils parlent de la MÊME entreprise/acteur (ex: Alstom, LVMH, Apple, etc.)
- ET ils concernent le MÊME événement/annonce (ex: inauguration, résultats, acquisition)
- Même si les titres sont formulés différemment
- Même si les sources sont différentes (BFM vs Boursier = même événement)

EXEMPLES DE DOUBLONS À FUSIONNER :
✓ "Apple annonce ses résultats Q4" + "Résultats trimestriels d'Apple" → DOUBLON (même événement)
✓ "Tesla double ses ventes" + "Tesla publie résultats records" → DOUBLON (même annonce)
✓ "Alstom inaugure un centre" + "Alstom ouvre une usine" → Si même centre/usine = DOUBLON

EXEMPLES QUI NE SONT PAS DES DOUBLONS :
✗ "Apple annonce résultats" + "Apple lance nouveau produit" → 2 annonces distinctes
✗ "Total en France" + "Total au Brésil" → Même entreprise mais contextes géographiques distincts
✗ "Tesla Model 3" + "Tesla Model Y" → Même entreprise mais produits différents

CE QUE TU DOIS FAIRE
1. IDENTIFIER les doublons selon les critères ci-dessus
2. FUSIONNER les doublons en un seul article de qualité :
   - Choisir le meilleur titre (le plus précis et informatif)
   - REFORMULER le contenu en combinant toutes les informations uniques
   - Ne perdre AUCUNE information factuelle (chiffres, dates, noms, contexte)
   - Produire un paragraphe fluide et narratif (pas une liste de faits)
3. CONSERVER tels quels les sujets uniques (pas de doublons)
4. Respecter le même TON et STYLE que les exemples ci-dessous

TON ET STYLE (IMPORTANT)
- Factuel mais narratif, pas robotique ni liste à puces
- Tous les chiffres conservés et précis
- Contexte business/géopolitique/sectoriel intégré naturellement
- Ton professionnel mais accessible
- Phrases fluides et variées
- Ne JAMAIS copier-coller des phrases sources

RÈGLES STRICTES
- ⚠️ REFORMULER lors de la fusion : utiliser tes propres mots, phrases fluides
- ⚠️ CONSERVER IDENTIQUES : tous les chiffres, montants, dates, noms propres
- Être AGRESSIF sur la détection : en cas de doute, c'est probablement un doublon
- Ne PAS inventer d'informations ou de chiffres
- Ne PAS ajouter d'analyse ou d'opinion personnelle
- Produire des paragraphes narratifs, pas des listes de faits
- Sortie en texte brut uniquement, sans JSON, sans markdown, sans numérotation

LANGUE
FR

FORMAT DE SORTIE (EXACT)
Titre du sujet 1
Paragraphe détaillé du sujet 1 avec toutes les informations consolidées et reformulées.

Titre du sujet 2
Paragraphe détaillé du sujet 2.

EXEMPLES CONCRETS DE QUALITÉ ATTENDUE APRÈS FUSION

EXEMPLE 1 — Deal stratégique (qualité cible)
Titre : Disney investit 1 milliard de dollars dans OpenAI
Paragraphe : Disney investit 1 milliard de dollars dans OpenAI, dans le cadre d'un deal qui permettra à Sora, son générateur d'images, d'utiliser près de 200 personnages Disney dans ses vidéos. Ce partenariat donne aussi la possibilité à Disney de monter en puissance au capital d'OpenAI à l'avenir. Par contre, Disney interdit à OpenAI d'entraîner son modèle IA sur sa galerie de personnages. En tout cas, vous connaissez le refrain : grâce aux deux lettres magiques, l'accord a réjoui Wall Street et l'action Disney, qui avait perdu 2,3% cette année, a retrouvé un peu de couleurs après l'annonce (+ 2%).

EXEMPLE 2 — Inauguration industrielle (qualité cible)
Titre : Verkor inaugure sa Mega factory
Paragraphe : Verkor, la pépite française des batteries, inaugure une gigafactory à Dunkerque. Elle représente un investissement de… 1,5 milliard, pour 1 200 emplois attendus. Si deux années de travaux auront été nécessaires, le plus dur reste à faire : comme les batteries électriques sont extrêmement difficiles à produire à échelle, l'étape de lancement des usines s'appelle "la vallée de la mort". Et elle a déjà eu raison du pionnier de la batterie électrique en Europe, le Suédois Northvolt. Résultat, Renault, qui s'est réservé les ¾ du potentiel de production de cette gigafactory, a prévu un plan B : en attendant que l'usine de Dunkerque monte en puissance, elle ira chercher ses batteries d'Alpine chez le coréen LG. Mais bon, pour l'instant, pas de médisances : l'aventure de la gigafactory ne fait que commencer.

EXEMPLE 3 — Actualité géopolitique (qualité cible)
Titre : Accord de paix Russie-Ukraine ?
Paragraphe : Pour la première fois (et à contre-cœur), les alliés de l'Ukraine évoquent l'éventualité que Kiev cède du terrain à la Russie dans le cadre d'un accord de paix. C'est le chancelier allemand F. Merz qui a lâché cette bombe, après s'être entretenu avec V. Zelensky puis D. Trump et enfin le secrétaire de l'Otan, M. Rutte - oui, F. Merz subit le fléau de la réunionite. Mais il n'a pas précisé de quel territoire il parlait : du Donbass, déjà en partie occupé par l'armée Russe ? De la Crimée, que la Russie considère comme annexée depuis 2014 ? Ou de parties encore épargnées par les bottes russes ? En tout cas, si les négo s'enchaînent et que les plans de paix s'accumulent, les affrontements sur le terrain sont, eux, toujours aussi violents.

CE QUI FAIT LA QUALITÉ DE CES EXEMPLES :
✓ Tous les chiffres sont précis et conservés (1 milliard, 2,3%, 1,5 milliard, 1 200 emplois, ¾)
✓ Le contexte business/géopolitique est intégré naturellement
✓ Le ton est factuel mais narratif, pas une liste sèche
✓ Les implications sont expliquées (impact bourse, plan B Renault, territoires en jeu)
✓ Aucune information n'est inventée, tout est factuel
✓ Les citations et noms sont présents et reformulés naturellement
✓ Phrases fluides et variées, pas répétitives
"""
