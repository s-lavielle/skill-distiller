---
name: skill-distiller
description: Crée un nouveau skill par distillation de sources existantes — fiche de sources, extraction fidèle, réconciliation (si plusieurs sources), document d'amendement, puis rédaction du skill final dans la langue cible et les conventions du projet. À utiliser quand l'utilisateur veut créer un skill à partir de sources (skills existants, documentations, articles) sans les reprendre tels quels.
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
  pas du contenu projet — jamais versionnés.
- **Périmètre** : les skills et artefacts produits visent le projet de la
  session. Un sujet qui vise un autre projet est signalé, pas traité en
  douce.
- **Lisibilité** : contenus structurés (titres, listes), phrases claires,
  terme technique utile **défini** à sa première occurrence — jamais de
  jargon étranger non traduit.
- **Justifier** chaque règle non évidente : le pourquoi, pas seulement le
  quoi.

## Artefacts

Répertoire de travail : `threads/<sujet>/`, à la racine du projet cible.

- **Nom par défaut** : `threads/` — le « fil de travail » : chaque
  artefact est le produit d'une étape du workflow, numéroté dans l'ordre.
- **Surchargé par l'utilisateur** : un autre nom de répertoire (conventions
  locales du projet cible, ou choix explicite au démarrage du travail)
  remplace `threads/` pour tout le lot.
- **Jamais versionné** : vérifier qu'il figure dans le `.gitignore` du
  projet cible, et l'y ajouter sinon.

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
  des fichiers de fabrication, pas du contenu projet — jamais versionnés.
- **Le processus s'amende lui-même** : ce qui a manqué pendant une
  exécution (ex. la réconciliation des sources multiples, ajoutée après
  coup) est intégré au skill — c'est ce qui le rend réutilisable.
