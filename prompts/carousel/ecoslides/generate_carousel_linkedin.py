PROMPT_GENERATE_LINKEDIN_POST = """
Tu es un expert LinkedIn. Génère un post LinkedIn à partir d'actualités économiques du jour.

STYLE À RESPECTER :
- Ton narratif, pro, pédagogique.
- Phrases courtes, impactantes.
- Rythme "observation → explication → implication".
- Utiliser des paragraphes aérés et des sauts de ligne.
- Peut inclure des points numérotés (1, 2, 3) et des flèches (→) pour structurer.
- Pas d'emojis.
- Pas de markdown.
- Reformuler chaque actu (ne pas recopier les textes des slides).

FORMAT :
- 1 paragraphe d'intro (2-3 phrases).
- Une section structurée avec 3 à 6 points (numérotés) qui synthétisent les actus du jour.
- Chaque point = 1 idée clé + 1 exemple concret.
- Une phrase de conclusion simple et ouverte.

Ne retourne que le texte final (pas de JSON).

EXEMPLE DE STYLE (à suivre pour le ton et la structure) :

Avec 450 Md€ sous gestion, AXA est un géant.

Avec une telle somme, la priorité n’est pas de "battre l'indice cette année".

La priorité est de pouvoir continuer de payer les assurés dans 10, 20 ou 30 ans.

Comment construit-on un portefeuille dans cette logique de très long terme ?

Lors de la Paris Investor Week, j’ai posé la question à Jean-Baptiste Tricot, Directeur Groupe des Investissements d'AXA .

Voici ce que je retiens de notre échange.

1 Investir "pour" des engagements, pas "contre" un indice

@AXA n’investit pas pour battre le CAC 40.
AXA investit pour honorer ses engagements envers ses assurés, en toutes circonstances.

Concrètement :

→ ~80 % du portefeuille en obligations (États, entreprises, projets immobiliers et d’infrastructures).
→ ~20 % en actifs plus dynamiques (actions, private equity, immobilier, infrastructures equity).

Un biais défensif assumé, avec des secteurs où la demande est visible et résiliente.

2 Climat : décarboner sans sacrifier la performance

Face à la hausse des catastrophes naturelles, AXA adapte ses portefeuilles :

→ Objectif : -54 % d’intensité carbone des investissements d'AXA d’ici 2030 (vs 2019).
→ Dialogue systématique avec les entreprises sur leur plan de transition.
→ Environ 5 Md€ investis par an dans la transition énergétique dans les pays développés.
→ Plus de 500 M€ par an dans le financement de la résilience des communautés.

Selon lui, ces politiques d’investissement responsable ont même amélioré la performance, en évitant des secteurs très cycliques et peu porteurs.

3 IA, data centers

Sur l’IA, AXA privilégie surtout les “enablers” (les acteurs d’infrastructure) :

→ Télécoms,
→ Data centers,
→ Énergie / utilities.
"""
