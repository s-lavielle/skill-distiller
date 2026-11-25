# Séquences de travail

> Comment le workflow se déroule concrètement, **dans l'ordre**, avec
> les commandes à lancer et les interventions humaines. Deux cas :
> une **distillation initiale** (créer un skill) et une
> **réintégration** (le faire évoluer quand ses sources bougent).
>
> Conventions communes : commandes lancées depuis la **racine du projet
> cible**, `<sujet>` nommant le lot (`threads/<sujet>/` par défaut,
> racine surchargeable par `--dir`). Les étapes détaillées du workflow
> sont dans [`../SKILL.md`](../SKILL.md).

## Cas 1 — Distillation initiale

*Situation : créer un skill « tickets GitLab » à partir de deux skills
existants et d'une doc, dans le projet cible.*

### 1. Ouvrir le lot

```
node <chemin>/bin/skill-distiller init tickets-gitlab
```

Crée `threads/tickets-gitlab/` (artefacts 00, 02, 04, 05 pré-remplis
depuis `templates/`, plus le répertoire `sources/`) et ajoute `threads/`
au `.gitignore` du projet.

*Humain* : rien — sauf `--dir atelier` si les conventions du projet
imposent un autre répertoire de travail.

### 2. Étape 1 — Fiche de sources

*Agent* : remplit `00-fiche-sources.yaml` — une entrée par source
(`ref`, `langue`, `points_a_retenir` **précis**, `ignorer`) ; **fige
chaque source** : copie le contenu lu dans `sources/<id>/` et renseigne
`snapshot:` et `date_fige:`.

*Humain* : **validation obligatoire de la fiche** — ce qu'on veut tirer
de chaque source, ce qu'on ignore, la langue cible. Sans son accord, on
ne va pas plus loin.

### 3. Étape 2 — Synthèse brute

*Agent* : rédige `01-synthese-brute.md` — extraction fidèle reformulée
dans la langue cible, **chaque point tracé à sa source** (marqueurs
comme `[T]`, `[C]`…), ambiguïtés et contradictions signalées en fin.
Rien d'inventé.

*Humain* : relecture, remarques au fil de l'eau.

### 4. Étape 3 — Réconciliation *(uniquement si plusieurs sources)*

*Agent* : rédige `02-reconciliation.md` — points communs, divergences
avec leurs éléments d'arbitrage et une recommandation.

*Humain* : **arbitrage** — chaque divergence tranchée, avec sa raison.

*Agent* : génère `03-synthese-reconciliee.md` — chaque règle retenue est
tracée (source retenue / écartée / pourquoi).

*Source unique : l'étape est sautée — la synthèse brute fait foi.*

### 5. Étape 4 — Amendements

*Agent* : remplit `04-amendements.md` — **Ajouts** (ce qui manque aux
sources : spécificités d'outil, règles du projet), **Amendements**
(cible / contenu / conséquence), **Cadre** (langue, ton, conventions,
traçabilité, structure).

*Humain* : **choix explicites**, au fil de la relecture — une remarque
peut amender une règle déjà posée.

### 6. Étape 5 — Skill final

```
node <chemin>/bin/skill-distiller new tickets-gitlab
```

Génère l'ossature de `05-skill-final.md` depuis la synthèse amendée :
déroulé dérivé des points tracés, note de sources depuis la fiche.

*Agent* : complète, justifie chaque règle non évidente, définit les
termes techniques à leur première occurrence.

*Humain* : relecture finale.

### 7. Contrôle

```
node <chemin>/bin/skill-distiller check tickets-gitlab
```

Doit finir sur `0 erreur(s)` : étapes complètes, chaque point tracé à
une source, amendements cohérents, front-matter rempli.

*Humain* : s'il reste des `✗`, corriger (ou faire corriger) et
**relancer jusqu'au vert**.

### 8. Installation

*Humain* : **décision d'installation** — déposer le skill dans le
répertoire de skills du projet cible. C'est une décision distincte de
la fabrication.

## Cas 2 — Réintégration (mise à jour)

*Situation : une source du lot `threads/tickets-gitlab/` a évolué (le
skill d'origine a été mis à jour) ; on veut faire évoluer le skill
distillé sans le refaire.*

### 1. État des sources

```
node <chemin>/bin/skill-distiller diff tickets-gitlab
```

Crée `reintegrations/<date>/01-etat-des-sources.md` : par source,
`identique`, `modifié (n modifiés, n nouveaux, n supprimés)` avec son
`diff-<id>.patch`, `à rafraîchir` ou `non figée`.

### 2. Rafraîchir ce qui ne l'est pas automatiquement

Si le rapport dit `à rafraîchir` : récupérer le contenu **actuel** de la
source (web, `git pull` du dépôt source…), le déposer dans
`threads/tickets-gitlab/sources-actuelles/<id>/`, puis **relancer
`diff`**. Pour une URL brute : `diff --fetch`.

⚠️ La copie figée (`sources/<id>/`) ne se touche jamais : c'est la
référence de comparaison.

### 3. Décision de poursuivre

*Humain* : tout est `identique` → arrêt ; sinon, on entre dans le cycle
`reintegrations/<date>/`.

### 4. Synthèse des nouveautés

*Agent* : rédige `02-synthese-nouveautes.md` — extraction fidèle des
**seuls changements**, tracée à leur source. Rien d'inventé : ce qui n'a
pas bougé n'est pas réécrit.

*Humain* : relecture.

### 5. Arbitrage

*Agent* : remplit `03-amendements.md` — pour chaque nouveauté : retenir,
écarter ou amender. La **cible est une règle existante** du skill final.

*Humain* : **décisions explicites**, avec leurs raisons.

### 6. Skill final vN

*Agent* : rédige `04-skill-final.md` — le skill mis à jour, autonome,
avec une **note de sources datée** : ce qui a changé, ce qui est retenu,
ce qui est écarté et pourquoi.

*Humain* : relecture, puis **décision de mise en place** (remplacer la
version installée).

### 7. Suite

L'historique reste dans `reintegrations/` : le cycle suivant partira du
nouvel état des sources.

## Points de validation humaine — récapitulatif

| Moment | Décision de l'humain |
|---|---|
| Fiche de sources (étape 1) | Validation obligatoire avant toute suite |
| Synthèse (étape 2) | Relecture, remarques |
| Réconciliation (étape 3) | **Arbitrage** des divergences |
| Amendements (étape 4) | **Choix explicites**, au fil de la relecture |
| Skill final (étape 5 / cycle) | Relecture, **décision d'installation / de mise en place** |
| Réintégration, étape 3 | Décision de poursuivre ou non |

## Limite connue

`check` contrôle le **lot initial** (00→05) : il ne couvre pas encore
les artefacts d'un cycle de réintégration. Leur cohérence repose sur la
même discipline de traçabilité, mais pas encore sur un contrôle
mécanique — un `check --cycle` serait un bon candidat d'évolution.
