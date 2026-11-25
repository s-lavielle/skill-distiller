# Repositories de skills connus

> Public : utilisateurs et contributeurs de `skill-distiller`.
> Première rédaction : 2026-11-24 (migrée d'opencode-boilersuit le
> 2026-11-25).

## Rôle

Un **registre de découverte** des dépôts qui hébergent des collections de
skills : il garde la trace des sources repérées, avec leur état de
vérification, pour servir de point de départ quand il s'agira de
**distiller de nouveaux skills** à partir de ces dépôts (le workflow est
décrit dans [`SKILL.md`](../SKILL.md)).

Aucune fonctionnalité ne consomme ce registre pour l'instant : il est
volontairement minimal, en attente d'un usage futur (découverte,
ingestion par la CLI).

## Fichier

La liste vit dans [`src/skill-repositories.yaml`](../src/skill-repositories.yaml) :
un contenu, un endroit — le présent document explique le mécanisme et n'y
est pas dupliqué.

## Champs d'une entrée

| Champ | Contenu |
|---|---|
| `id` | Identifiant unique de l'entrée, forme `<owner>-<nom-en-kebab>`. Clé stable du registre. |
| `name` | Nom du dépôt. |
| `owner` | Propriétaire ou organisation du dépôt. |
| `url` | URL du dépôt. |
| `type` | Nature du dépôt (voir ci-dessous). |
| `scope` | Domaines couverts, en liste (minuscules, tirets bas). |
| `description` | Ce que contient le dépôt, en une phrase. |
| `verification` | État de vérification de l'entrée (voir ci-dessous). |

## Types de dépôt

- `skills_collection` — collection de skills ;
- `skills_library` — bibliothèque organisée par domaines ;
- `skill_system_orchestrator` — système avec orchestration de skills ;
- `personas_and_skill_bundles` — personas et bundles de rôles/skills ;
- `index_catalogue` — index d'autres dépôts : source de découverte, à ne
  pas importer en bloc.

## États de vérification

- `verified_current_search` — dépôt vérifié lors de la recherche courante ;
- `verified_in_prior_search` — dépôt vérifié lors d'une recherche
  antérieure ;
- `url_needs_validation` — URL non confirmée : à **exclure de toute
  ingestion automatisée** tant qu'elle n'est pas validée.

## Ajouter une entrée

1. Ajouter l'entrée dans `src/skill-repositories.yaml`, avec un `id`
   inédit ;
2. Renseigner `verification` selon l'état réel de contrôle du dépôt ;
3. Un dépôt à l'URL incertaine reste `url_needs_validation` et n'est pas
   utilisable pour un import automatisé.

## Usage futur

Quand une fonctionnalité d'ingestion existera, elle consommera ce
registre comme liste de sources. Les entrées `url_needs_validation` en
seront exclues jusqu'à validation de leur URL.
