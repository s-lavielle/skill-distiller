---
name: skill-distiller
description: Crée un nouveau skill par distillation de sources existantes — fiche de sources, extraction fidèle, réconciliation (si plusieurs sources), document d'amendement, puis rédaction du skill final dans la langue cible et les conventions du projet ; et le fait évoluer quand ses sources bougent (réintégration). À utiliser quand l'utilisateur veut créer un skill à partir de sources (skills existants, documentations, articles) sans les reprendre tels quels, ou mettre à jour un skill déjà distillé.
---

# Distillation d'un skill à partir de sources

## Objectif

Produire un nouveau skill **maîtrisé** : on ne reprend jamais un skill
étranger tel quel (boîte noire, langue, conventions inconnues) — on lit
les sources comme une **inspiration**, on en extrait la substance, et on
rédige un skill dont chaque règle est tracée : soit elle vient d'une
source, soit elle est un choix explicite de l'utilisateur.

Deux registres restent séparés jusqu'à la rédaction finale :

- **la synthèse** : ce que disent les sources, reformulé en langue cible ;
- **l'amendement** : les choix de l'utilisateur, explicites et datés.

Le skill final les fusionne — sans jamais mélanger les deux en silence.

## Principes

- **Valider chaque étape avec l'utilisateur** avant de poursuivre
  (fiche, synthèse, réconciliation, amendements) : pas de phase longue
  en silence.
- **Artefacts dans un répertoire de travail dédié** du projet cible,
  `threads/<sujet>/` par défaut : ce sont des fichiers de fabrication,
  pas du contenu projet. Ils sont **conservés en entier** (sources
  figées, historique des réintégrations) mais **jamais versionnés** :
  la solution est versionnée dans un dépôt, pas ses produits.
- **Périmètre** : les skills et artefacts produits visent le projet de la
  session. Un sujet qui vise un autre projet est signalé, pas traité en
  douce.
- **Lisibilité** : contenus structurés (titres, listes), phrases claires,
  terme technique utile **défini** à sa première occurrence — jamais de
  jargon étranger non traduit.
- **Justifier** chaque règle non évidente : le pourquoi, pas seulement le
  quoi.

## Exécution des commandes

Les commandes de la CLI (`init`, `check`, `diff`, `new`) s'exécutent de
trois façons, dans cet ordre de préférence :

1. **outils MCP** `skill_distiller_*` quand l'environnement de l'agent y
   est connecté — le serveur de skill-distiller les expose, en même
   temps que ce skill ;
2. **CLI directe** : `python3 <chemin>/bin/skill-distiller <commande>
   <sujet>`, depuis la racine du projet cible ;
3. **Docker** : `docker compose exec skill-distiller skill-distiller
   <commande> <sujet>` (voir le README).

Quelle que soit la voie, la commande agit **sur le projet cible** : les
artefacts y sont écrits, jamais dans le dépôt de skill-distiller.

## Artefacts

Répertoire de travail : `threads/<sujet>/`, à la racine du projet cible.

- **Nom par défaut** : `threads/` — le « fil de travail » : chaque
  artefact est le produit d'une étape du workflow, numéroté dans l'ordre.
- **Surchargé par l'utilisateur** : un autre nom de répertoire (conventions
  locales du projet cible, ou choix explicite au démarrage du travail)
  remplace `threads/` pour tout le lot.
- **Jamais versionné** : vérifier qu'il figure dans le `.gitignore` du
  projet cible, et l'y ajouter sinon. Conservé en entier sur disque : la
  mémoire du lot (sources figées, cycles de réintégration) en fait partie.

Sous-répertoires du lot :

- `sources/<id>/` — **copie figée** de chaque source, telle qu'elle était
  au moment de la distillation (étape 1). C'est elle qui rend possible la
  réintégration quand les sources bougent.
- `reintegrations/<horodatage>/` — un sous-répertoire par **cycle de
  réintégration** (état des sources, synthèse des nouveautés, amendements,
  skill final vN). L'historique est conservé comme le reste du lot.

| Fichier | Étape | Contenu |
|---|---|---|
| `00-fiche-sources.yaml` | 1 | les sources, leurs points à retenir, la langue cible |
| `01-synthese-brute.md` | 2 | l'extraction fidèle, reformulée, tracée aux sources |
| `02-reconciliation.md` | 3 | (si plusieurs sources) convergences, divergences, arbitrages |
| `03-synthese-reconciliee.md` | 3 | (si plusieurs sources) la synthèse après arbitrage |
| `04-amendements.md` | 4 | ajouts, amendements, cadre — les choix de l'utilisateur |
| `05-skill-final.md` | 5 | le skill rédigé, autonome |

Le document de synthèse qui alimente l'étape 4 est `01-synthese-brute.md`
(sources uniques) ou `03-synthese-reconciliee.md` (sources multiples).

## Étape 1 — Fiche de sources

Une entrée par source (modèle : `templates/fiche-sources.yaml`) :

```yaml
sources:
  - ref: <URL ou chemin>
    langue: <langue de la source>
    snapshot: sources/<id>/   # copie figée (étape 1)
    date_fige: <AAAA-MM-JJ>
    points_a_retenir:
      - <ce qu'on veut en tirer, spécifiquement>
    ignorer:
      - <ce qui ne concerne pas le projet>
langue_cible: français   # défaut ; le champ est conservé
```

- Les `points_a_retenir` sont **spécifiques** : des règles, des processus,
  des garde-fous visés — pas un résumé vague de la source.
- `ignorer` évite de rapporter l'habillage, le marketing ou les
  spécificités d'outil qui ne concernent pas le projet.
- **Figer la source** : copier le contenu lu (skill source, document)
  dans `sources/<id>/`, et renseigner `snapshot:` et `date_fige:` dans la
  fiche. Sans cette copie figée, aucune réintégration ne sera possible.
- La **langue cible** est le français par défaut.

Présenter la fiche à l'utilisateur et attendre sa validation avant de
poursuivre.

## Étape 2 — Synthèse brute (extraction fidèle)

Produire `01-synthese-brute.md` :

- la substance des sources — règles de fond, étapes de processus,
  garde-fous, formats de sortie — reformulée en langue cible ;
- **chaque point tracé à sa source** (marqueur, ex. `[T]` pour une source
  « to-tickets ») ;
- **rien d'inventé, rien de perdu** : c'est la fidélité qui compte ici,
  pas le style ;
- signaler explicitement en fin de document : ambiguïtés de langue (les
  subtilités qui ne se traduisent pas d'un mot), contradictions entre
  sources, ce qui a été mis de côté et pourquoi.

Présenter la synthèse à l'utilisateur : il la relit et fait ses remarques
au fil de l'eau.

## Étape 3 — Réconciliation (si plusieurs sources)

**Seulement quand plusieurs sources sont en jeu.** Produire
`02-reconciliation.md` (modèle : `templates/reconciliation.md`) :

1. **Points communs** : ce que les sources disent à l'unisson → une
   règle unique suffit (dédoublonnage).
2. **Différences à arbitrer** : ce sur quoi les sources divergent ou se
   recouvrent partiellement → chaque divergence est posée avec ses
   **éléments d'arbitrage** : ce que propose chaque source, les
   conséquences de chaque option, une recommandation.
3. **Arbitrage** : présenter les divergences à l'utilisateur (les
   décisions qui engagent la suite sont posées comme des choix
   explicites), consigner chaque décision et sa raison.

Générer ensuite `03-synthese-reconciliee.md` : la synthèse complète où
chaque règle retenue est tracée — source retenue, source écartée,
pourquoi. C'est ce document qui alimente l'étape 4.

Avec une source unique, cette étape est sautée : la synthèse brute est le
document de synthèse.

## Étape 4 — Document d'amendement

Produire puis remplir `04-amendements.md` (modèle :
`templates/amendements.md`), au fil de la relecture de l'utilisateur.
Trois sections :

- **Ajouts** : règles ou notions **absentes des sources** mais nécessaires
  — spécificités de l'outil cible (ex. GitLab), règles internes du projet,
  exigences métier.
- **Amendements** : ce qui **modifie** la synthèse. Chaque entrée porte sa
  *cible* (la section visée), son *contenu* et sa *conséquence* (ce que ça
  change dans le skill).
- **Cadre** : langue cible, ton, conventions du projet à respecter,
  traçabilité (le skill cite-t-il ses sources ?), structure du skill final.

Rien n'est figé : les amendements se complètent au fil des remarques, et
une remarque de l'utilisateur peut amender une règle déjà posée.

## Étape 5 — Rédaction du skill final

Produire `05-skill-final.md` (structure : `templates/skill-final.md`) à
partir de la synthèse amendée :

- le **format des skills du projet cible** : front-matter `name` /
  `description`, déroulé numéroté, rappels en fin ;
- **autonome** : utilisable sans lire les sources ni les artefacts de
  fabrication ;
- chaque règle **justifiée** quand elle n'est pas évidente ;
- vocabulaire de la langue cible ; un terme technique utile est **défini**
  à sa première occurrence — ne pas laisser de jargon étranger non traduit ;
- une note de fin nomme les **sources d'inspiration**, pour l'entretien
  futur du skill.

Le dépôt du résultat et **son installation sont une décision distincte**,
à prendre avec l'utilisateur.

## Faire évoluer le skill — réintégration

Les sources bougent après la distillation : le skill source est mis à
jour, la doc évolue. Sans boucle de retour, le skill distillé dérive
silencieusement de ses sources. La **réintégration** refait le processus
**sur les seuls changements** — jamais une recopie, jamais un refus
silencieux de la nouveauté.

Un cycle = un répertoire `reintegrations/<horodatage>/` :

1. **État des sources** (`01-etat-des-sources.md`) — comparer chaque
   source actuelle à sa copie figée (`sources/<id>/`). La commande
   `skill-distiller diff <sujet>` produit le rapport — identique,
   modifié, nouveau, perdu — et les diffs. Une source que rien ne permet
   de résoudre automatiquement (URL ou référence descriptive) est
   d'abord rafraîchie : déposer le contenu actuel dans
   `sources-actuelles/<id>/`, puis relancer `diff`.
2. **Synthèse des nouveautés** (`02-synthese-nouveautes.md`) — extraction
   fidèle des **seuls changements**, tracée à leur source, dans la langue
   cible. Rien d'inventé : ce qui n'a pas bougé n'est pas réécrit.
3. **Arbitrage** (`03-amendements.md`) — pour chaque nouveauté : retenir,
   écarter ou amender. Un amendement de réintégration a pour **cible une
   règle existante** du skill final (modèle `templates/amendements.md`).
   Décisions explicites de l'utilisateur.
4. **Skill final vN** (`04-skill-final.md`) — le skill mis à jour,
   autonome, avec une note de sources **datée** : ce qui a changé, ce qui
   a été retenu, ce qui a été écarté et pourquoi.

La mise en place de la nouvelle version reste une décision distincte.
Tout le cycle est conservé : l'historique des réintégrations fait partie
de la mémoire du lot.

## Rappels

- **Ne jamais reprendre un skill étranger tel quel** : la valeur est dans
  la digestion, pas dans la copie.
- **Ne rien inventer** : ce qui n'est pas dans les sources est un choix —
  donc dans l'amendement, jamais fondu dans la synthèse.
- **Valider chaque étape** avant la suivante (fiche, synthèse,
  réconciliation, amendements) : pas de phase longue en silence.
- **La langue cible est le français par défaut** ; le champ est conservé
  pour les autres cas.
- **Les artefacts restent dans le répertoire de travail dédié** : ce sont
  des fichiers de fabrication, pas du contenu projet — conservés en
  entier, jamais versionnés (la solution est versionnée, pas ses
  produits).
- **Figer les sources à la lecture** : sans copie figée dans `sources/`,
  pas de réintégration possible.
- **Quand une source bouge, réintégrer** : refaire le processus sur les
  seuls changements, avec arbitrage humain — ne jamais laisser le skill
  dériver de ses sources en silence.
- **Le processus s'amende lui-même** : ce qui a manqué pendant une
  exécution (ex. la réconciliation des sources multiples, ajoutée après
  coup) est intégré au skill — c'est ce qui le rend réutilisable.
