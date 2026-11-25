# skill-distiller — *auditable skill synthesis*

Créer un skill **maîtrisé** à partir de sources existantes — sans jamais
les copier.

## Présentation

`skill-distiller` formalise une méthode de **création de skills par
distillation de sources** : skills existants, documentations, articles.
On ne reprend jamais un skill étranger tel quel (boîte noire, langue,
conventions inconnues) : on le lit comme une **inspiration**, on en
extrait la substance, on arbitre entre les sources, on y ajoute ses
propres règles, et on rédige un skill nouveau et autonome.

**Distillation** au sens alchimique : affiner des sources brutes en un
produit nouveau et maîtrisé — et non extraction de skills depuis des
trajectoires d'exécution (*trajectory mining*). La définition complète et
le pourquoi de la méthode : [`docs/methode.md`](docs/methode.md).

Le sous-titre du produit dit son exigence : ***auditable skill
synthesis*** — chaque règle du skill produit est tracée, soit à une
source, soit à un choix explicite de l'utilisateur.

## Le workflow

Cinq étapes, artefacts dans `threads/<sujet>/` (jamais versionné,
répertoire surchargeable) :

| Étape | Artefact | Contenu |
|---|---|---|
| 1 | `00-fiche-sources.yaml` | les sources, leurs points à retenir, la langue cible |
| 2 | `01-synthese-brute.md` | l'extraction fidèle, reformulée, tracée aux sources |
| 3 | `02-reconciliation.md` / `03-synthese-reconciliee.md` | (si plusieurs sources) divergences, arbitrages |
| 4 | `04-amendements.md` | ajouts, amendements, cadre — les choix de l'utilisateur |
| 5 | `05-skill-final.md` | le skill rédigé, autonome et justifié |

Chaque étape est validée avec l'utilisateur avant la suivante. Le détail :
[`SKILL.md`](SKILL.md).

## Contenu du dépôt

```
skill-distiller/
├── README.md                  ce fichier
├── SKILL.md                   le workflow 5 étapes, générique, multi-agents
├── templates/                 modèles d'artefacts (étapes 1, 3, 4, 5)
├── bin/
│   └── skill-distiller        CLI Node.js sans dépendance (init/check/new)
├── tests/                     tests de la CLI (node --test, sans dépendance)
├── src/
│   └── skill-repositories.yaml  registre de découverte de sources
├── examples/
│   └── tickets-gitlab/        cas réel complet (numérotation d'origine
│                              00→03, antérieure à la réconciliation)
├── conventions/
│   └── exemple-projet.md      greffon de conventions locales
└── docs/
    ├── methode.md             thèse → antithèse → synthèse, pourquoi
    │                          « distillation », place dans le paysage
    ├── etat-de-l-art.md       SkillFusion, Skill-Synthesizer, SkillGen,
    │                          Frankenstein, AutoSkill, survey 2608.29596
    └── skill-repositories.md  documentation du registre de sources
```

## Installation

Aucune dépendance : ni OpenCode, ni boilersuit — le format cible est le
**SKILL.md standard multi-agents**.

1. Récupérer le dépôt :

   ```
   git clone git@github.com:s-lavielle/skill-distiller.git
   ```

2. Utiliser le skill : installer `SKILL.md` (et ses `templates/`) dans le
   répertoire de skills de votre agent, ou le lire comme procédure et le
   faire suivre par l'agent de votre choix.

3. Greffer les conventions du projet cible :
   [`conventions/exemple-projet.md`](conventions/exemple-projet.md) —
   langue, ton, répertoire de travail, traçabilité, structure du skill
   final.

### CLI

Trois commandes, Node.js sans dépendance, à lancer **depuis la racine du
projet cible** :

```
node <chemin>/bin/skill-distiller init <sujet>    # [--dir <racine>]
node <chemin>/bin/skill-distiller check <sujet>   # [--dir <racine>]
node <chemin>/bin/skill-distiller new <sujet>     # [--force]
```

- `init <sujet>` — crée `threads/<sujet>/` (racine surchargeable par
  `--dir`, ex. `--dir atelier`), pré-remplit les artefacts depuis
  `templates/` et ajoute la racine au `.gitignore` du projet cible ;
- `check <sujet>` — vérifie la traçabilité : étapes complètes (00/01/04/05,
  plus 02/03 si plusieurs sources), chaque point de la synthèse tracé à
  une source, amendements cohérents (cible/contenu/conséquence), skill
  final rempli — code de sortie non nul si erreur ;
- `new <sujet>` — génère l'ossature du skill final depuis la synthèse
  amendée (déroulé dérivé des points tracés, note de sources depuis la
  fiche) ; `--force` pour régénérer un `05-skill-final.md` déjà rempli.

Les tests de la CLI se lancent avec `node --test tests/` (ou
`npm test`).

## Positionnement

- **Jamais de copie** : la valeur est dans la digestion, pas dans la
  réplication d'un skill étranger ;
- **Synthesis, pas composition** : on produit un nouvel artefact, on
  n'orchestre pas des skills à l'exécution (survey arXiv 2608.29596,
  §3.5) ;
- **Humain à chaque étape** : les arbitrages entre sources sont des
  décisions explicites, jamais des fusions silencieuses ;
- **Sources traquées** : registre de découverte
  [`src/skill-repositories.yaml`](src/skill-repositories.yaml)
  ([`docs/skill-repositories.md`](docs/skill-repositories.md)).

## Exemple

Un cas réel complet — créer un skill de création de tickets GitLab à
partir d'une demande : [`examples/tickets-gitlab/`](examples/tickets-gitlab/).

## État de l'art

SkillFusion, Skill-Synthesizer, SkillGen, Frankenstein, AutoSkill :
[`docs/etat-de-l-art.md`](docs/etat-de-l-art.md).
