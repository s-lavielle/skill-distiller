# skill-distiller — *auditable skill synthesis*

Créer un skill **maîtrisé** à partir de sources existantes — sans jamais
les copier — et le **faire évoluer** quand ses sources bougent.

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

Le skill produit vit : les sources sont **figées** à la distillation
(copie conservée dans le lot), et quand elles bougent, la
**réintégration** refait le processus sur les seuls changements —
`skill-distiller diff` en donne l'état. Voir [`SKILL.md`](SKILL.md)
(« Faire évoluer le skill ») et [`docs/methode.md`](docs/methode.md).

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
[`SKILL.md`](SKILL.md). Le déroulé pas à pas — commandes à lancer et
interventions humaines, distillation initiale comme réintégration :
[`docs/sequences-de-travail.md`](docs/sequences-de-travail.md).

## Contenu du dépôt

```
skill-distiller/
├── README.md                  ce fichier
├── SKILL.md                   le workflow 5 étapes, générique, multi-agents
├── Dockerfile                 image de la CLI (Python 3, git, curl)
├── docker-compose.yml         service pour lancer la CLI sur un projet
│                              cible monté en volume, service MCP
├── .dockerignore
├── templates/                 modèles d'artefacts (étapes 1, 3, 4, 5)
├── bin/
│   └── skill-distiller        CLI Python 3 sans dépendance
│                              (init/check/diff/new, mcp)
├── tests/                     tests de la CLI et de la façade MCP
│                              (unittest, sans dépendance)
├── src/
│   ├── mcp_server.py          façade MCP : sert la CLI, le skill et
│   │                          les lots aux agents (stdio ou HTTP)
│   └── skill-repositories.yaml  registre de découverte de sources
├── examples/
│   └── tickets-gitlab/        cas réel complet (numérotation d'origine
│                              00→03, antérieure à la réconciliation)
├── conventions/
│   └── exemple-projet.md      greffon de conventions locales
└── docs/
    ├── methode.md             thèse → antithèse → synthèse, pourquoi
    │                          « distillation », place dans le paysage
    ├── sequences-de-travail.md  déroulé pas à pas : commandes et
    │                          interventions humaines (initiale, maj)
    ├── etat-de-l-art.md       SkillFusion, Skill-Synthesizer, SkillGen,
    │                          Frankenstein, AutoSkill, survey 2608.29596
    └── skill-repositories.md  documentation du registre de sources
```

**Hors versionné** (conservé sur disque, jamais commité) : `tmp/` (fichiers
d'échange), `.idea/`, `threads/` (lots de distillation) et `agent/`
(contexte et knowledge de l'agent).

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

Quatre commandes de workflow, **Python 3 (≥ 3.9) sans dépendance**
(bibliothèque standard seule), à lancer **depuis la racine du projet
cible** :

```
python3 <chemin>/bin/skill-distiller init <sujet>    # [--dir <racine>]
python3 <chemin>/bin/skill-distiller check <sujet>   # [--dir <racine>]
python3 <chemin>/bin/skill-distiller diff <sujet>    # [--fetch]
python3 <chemin>/bin/skill-distiller new <sujet>     # [--force]
```

Une cinquième commande, `mcp`, sert ces commandes, le skill et le
contenu des lots aux agents compatibles : voir
[« Façade MCP »](#fa%C3%A7ade-mcp-pour-les-agents).

(Le script porte un shebang : `./bin/skill-distiller …` marche aussi.)

- `init <sujet>` — crée `threads/<sujet>/` (racine surchargeable par
  `--dir`, ex. `--dir atelier`), pré-remplit les artefacts depuis
  `templates/`, crée le répertoire `sources/` des copies figées et ajoute
  la racine au `.gitignore` du projet cible ;
- `check <sujet>` — vérifie la traçabilité : étapes complètes (00/01/04/05,
  plus 02/03 si plusieurs sources), chaque point de la synthèse tracé à
  une source, amendements cohérents (cible/contenu/conséquence), skill
  final rempli — code de sortie non nul si erreur ;
- `diff <sujet>` — compare les sources figées (`sources/<id>/`) aux
  sources actuelles (ref locale, ou `sources-actuelles/<id>/` après
  rafraîchissement manuel, ou URL avec `--fetch`) et produit
  `reintegrations/<date>/01-etat-des-sources.md` avec les diffs : c'est la
  première étape de la réintégration ;
- `new <sujet>` — génère l'ossature du skill final depuis la synthèse
  amendée (déroulé dérivé des points tracés, note de sources depuis la
  fiche) ; `--force` pour régénérer un `05-skill-final.md` déjà rempli.

Les tests de la CLI se lancent avec `python3 -m unittest discover -s tests`.

### Conteneurisation

Un `Dockerfile` et un `docker-compose.yml` permettent d'exécuter la CLI
sans installer Python sur l'hôte. L'image embarque **Python 3, git et
curl** (git pour les opérations sur le projet cible monté, curl pour le
diagnostic réseau de `diff --fetch`).

Construire l'image :

```
docker build -t skill-distiller .
```

Une image pré-construite est publiée sur GHCR (workflow
`.github/workflows/image.yml`, tags `latest` + version + SHA) :

```
docker pull ghcr.io/s-lavielle/skill-distiller:latest
```

**Modèle compose — conteneur longue durée** : le service reste en vie, la
CLI s'exécute par `exec` sans recréer de conteneur à chaque commande. Le
projet cible est monté en `/work`, répertoire de travail du conteneur
(donc la racine attendue par la CLI) :

```
docker compose up -d
docker compose exec skill-distiller skill-distiller init <sujet>
docker compose exec skill-distiller skill-distiller check <sujet>
docker compose down
```

Le projet cible se précise avec la variable `TARGET_PROJECT` (défaut : le
répertoire courant) :

```
TARGET_PROJECT=/chemin/vers/projet-cible docker compose up -d
```

**Usage ponctuel** (sans compose) : un conteneur par commande, détruit à
la fin :

```
docker run --rm -v /chemin/vers/projet-cible:/work skill-distiller diff <sujet> --fetch
```

Les tests de la CLI se lancent dans le conteneur :

```
docker compose exec skill-distiller python3 -m unittest discover -s /opt/skill-distiller/tests
```

### Façade MCP (pour les agents)

Le produit reste un outil autonome (la CLI ci-dessus) ; la façade MCP en
est la **prise standard** qui le rend branchable par n'importe quel
agent compatible (Claude Code, VS Code, Codex…). Elle sert les trois
facettes du produit par le même connecteur :

- **outils de commande** : `skill_distiller_init`, `_check`, `_diff`,
  `_new` — mêmes sémantiques que les commandes CLI (chaque appel exécute
  la commande, pas de logique dupliquée) ;
- **outils de contenu** : `skill_distiller_state` (inventaire du lot),
  `_read` (récupérer un artefact ou une source), `_write` (**rendre un
  résultat**) — le lot se consulte et se rend entièrement par le MCP ;
- **skill** : `SKILL.md` + `templates/` servis au format Agent Skills
  (extension MCP Skills, `skill://skill-distiller/…`), avec leurs
  digests SHA-256 — le workflow est distribué par l'outil lui-même,
  versionné avec lui.

Pour `write`, l'agent ne choisit pas de chemin : il **étiquette** son
résultat, et c'est skill-distiller qui le range au bon endroit du lot —
`fiche`, `synthese-brute`, `reconciliation`, `synthese-reconciliee`,
`amendements`, `skill-final`, `source:<id>/<fichier>`,
`source-actuelle:<id>/<fichier>`, `cycle:<date>:<artefact>`. Les
équivalences vers les fichiers (`00-fiche-sources.yaml`, `sources/<id>/`,
`reintegrations/<date>/`…) sont l'affaire de l'outil.

Deux transports :

```
python3 <chemin>/bin/skill-distiller mcp                      # stdio
python3 <chemin>/bin/skill-distiller mcp --http 0.0.0.0:8080  # URL
```

- **stdio** : l'agent lance la commande lui-même (l'outil est installé
  là où l'agent tourne) — pas de serveur, pas de réseau ;
- **HTTP streamable** : le conteneur expose une URL pour les agents qui
  ne peuvent rien lancer. Avec le compose, le service
  `skill-distiller-mcp` partage `/work` (le projet cible) et se joint
  depuis un autre conteneur du réseau :

  ```
  docker compose up -d skill-distiller-mcp
  # depuis le conteneur du projet cible :
  #   http://skill-distiller-mcp:8080/mcp
  ```

Le service HTTP se pilote par l'environnement — un orchestrateur
quelconque n'a pas à connaître la CLI :

| Variable | Effet |
| --- | --- |
| `SKILL_DISTILLER_MCP_ADDR` | adresse par défaut de `--http` (ex. `0.0.0.0:8080`) — l'argument explicite reste prioritaire |
| `SKILL_DISTILLER_MCP_TOKEN` | jeton Bearer optionnel : avec la variable, toute requête `/mcp` sans `Authorization: Bearer <jeton>` est refusée (401) |

`GET /health` répond 200 : sonde de disponibilité pour Docker
`HEALTHCHECK`, Kubernetes ou tout superviseur. Elle reste accessible
sans jeton (elle ne révèle que l'existence du service).

**Mode nominal — « pur MCP »** : l'agent hôte n'a besoin d'aucun accès
disque. Il charge le skill, consulte le lot (`state`, `read`), fait le
travail selon le workflow, puis rend chaque résultat (`write`) : « voilà
la synthèse du lot X, range-la chez toi ». Tout reste chez
skill-distiller — un agent peut disparaître en cours de lot, une autre
session reprend sans rien d'autre que le MCP. L'agent peut conserver des
copies chez lui s'il le souhaite, mais rien n'en dépend.

Garde-fous : sept outils fixes (jamais de commande libre), paramètres
validés (sujet en slug, `dir` sur un seul segment, `project` limité à un
répertoire existant), **écriture de contenu confinée au lot** (références
validées, aucun échappement de chemin, plafond de 512 KiB par contenu),
ressources du skill servies depuis une liste fermée. Le projet cible est
celui monté en `/work` (ou précisé par l'outil, paramètre `project`).
Un code de sortie non nul de la CLI est rendu en `isError` — par exemple
`check` avec des erreurs restantes.

⚠️ Sans `SKILL_DISTILLER_MCP_TOKEN`, l'endpoint n'embarque **pas**
d'authentification : restez sur un réseau de confiance (le réseau
interne du compose). Une exposition publique exige le jeton ci-dessus ou
une couche d'authentification en amont.

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
