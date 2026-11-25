# État de l'art — skill synthesis

> Références repérées lors de la session de cadrage (2026-11-24/25) ;
> liens vérifiés le 2026-11-25. Pour le positionnement de fond, voir
> [`methode.md`](methode.md).

## Voisins directs — synthèse de skills en un nouvel artefact

### SkillFusion — arXiv 2610.15481

*SkillFusion: Towards Reliable Multi-Skill Composition for LLM Agents*
(Huang et al., 2026) — <https://arxiv.org/abs/2610.15481>

Compilation **hors-ligne** de plusieurs skills en un skill fusionné
réutilisable, avec réconciliation des interactions entre skills (conflits
durs, souples, redondances). C'est le pendant **automatisé** de notre
étape 3 (réconciliation) : même problème — arbitrer entre sources
divergentes — mais résolu par un compilateur, sans arbitrage humain.

### Skill-Synthesizer — Axiomatic AI

*Skill-Synthesizer: Query-Aware Skill Synthesis for Scientific Reasoning*
(McCarran et al., workshop ICML 2026) —
<https://openreview.net/forum?id=T3WDCimC5K>

Extraction des passages **pertinents** d'une bibliothèque de skills,
composés en un skill unique adapté à la requête. Notre champ
`points_a_retenir` (fiche de sources, étape 1) formalise la même idée —
viser ce qu'on veut tirer de chaque source, pas un résumé vague.

### SkillGen — arXiv 2605.10999

*SkillGen: Verified Inference-Time Agent Skill Synthesis* —
<https://arxiv.org/abs/2605.10999>

Production d'un skill **auditable** et **human-readable**, inspectable
avant usage, avec vérification empirique de son effet. C'est l'origine de
notre exigence de maîtrise : un skill doit pouvoir être lu, compris et
vérifié **avant** d'être installé. Attention toutefois : SkillGen distille
depuis des **trajectoires d'exécution** — sa matière première diffère de
la nôtre (sources écrites).

### Frankenstein (SkillAvatars)

Combiner les **meilleures parties** de plusieurs skills issus de dépôts
de skills. C'est notre registre de sources (`src/skill-repositories.yaml`)
plus le workflow, automatisés.

⚠️ **Référence à confirmer** : l'attribution « SkillAvatars » n'a pas pu
être vérifiée (SkillAvatars est une plateforme de découverte de skills ;
un projet « frankenstein » existe par ailleurs, sans lien établi).
À re-vérifier avant toute citation publique.

## L'autre « distillation » — depuis les trajectoires

### AutoSkill

AutoSkill (Yang et al., 2026) crée et met à jour des skills **en ligne**
depuis des trajectoires de conversation d'agents, selon un cycle
extraction – maintenance – réutilisation. C'est le sens *trajectory
mining* du mot distillation — notre repoussoir terminologique (voir
[`methode.md`](methode.md)).

## Cadrage général

### Survey — arXiv 2608.29596

*A Systematic Survey of Agentic Skills: Architecture, Lifecycle, and
Security* (Badhe et al., 2026) — <https://arxiv.org/abs/2608.29596>

§3.5 « Skill Composition and Synthesis » : la ligne de démarcation
**composition** (orchestration de skills à l'exécution) vs **synthesis**
(production d'un nouvel artefact). skill-distiller est du côté
*synthesis*.
