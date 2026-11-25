# 03 — Skill final (étape 2b) — brouillon de travail

> Généré à partir de `01-synthese-brute.md` amendée par
> `02-amendements.md`. Emplacement de travail : `tmp/` — ce n'est pas
> encore un skill installé (non placé dans `skills/`, non activable).
> Les choix assumés (A6, A7, cadre) sont à valider.

---

---
name: creer-tickets-gitlab
description: Découpe une demande en tickets GitLab selon les règles de création du projet — un ou plusieurs tickets principaux verticaux, découpés en sous-tickets horizontaux par compétence, adossés aux documents de ce qui a été vendu. À utiliser quand l'utilisateur demande de créer, préparer ou découper les tickets d'une demande ou d'une fonctionnalité.
---

# Création des tickets GitLab à partir d'une demande

Le découpage transforme une demande en tickets **créables et pilotables**,
sans jamais sortir de ce qui a été vendu. Deux niveaux structurent le
résultat : le **ticket principal** (vertical, validé par le client) et ses
**sous-tickets** (horizontaux, répartition du travail entre intervenants).

## Prérequis

1. **La demande à découper** : ce que l'utilisateur veut faire faire, en
   clair.
2. **Les documents de ce qui a été vendu** : cahier des charges initial,
   proposition commerciale et technique (clarifications, options retenues
   ou non), avenants (parties technique et commerciale). Ils sont
   accessibles par le **point d'accès** déclaré dans le contexte de la
   session.
   - Si le point d'accès est absent du contexte : **le demander** à
     l'utilisateur avant toute découpe. Ne jamais supposer, ne jamais
     inventer, ne jamais découper « de mémoire ».
3. **Le projet de la session est bien celui des tickets** : les tickets
   GitLab créés relèvent du dépôt déclaré dans le contexte projet
   (règle `perimetre-projet`).

## Déroulé

### 1. Lire la demande et confronter aux documents vendus

Lire intégralement la demande, puis les documents de référence. Pour chaque
fonctionnalité demandée, trancher :

- **référencée** dans les documents vendus → entre dans la découpe ;
- **non référencée** → **hors périmètre** : elle ne figure dans aucun
  ticket. La signaler explicitement à l'utilisateur (elle pourra donner
  lieu à un avenant ou à une validation explicite, hors de cette découpe).
- **ambiguë** (formulée dans les documents de façon imprécise) → poser la
  question plutôt que de trancher seul.

Le hors-périmètre est **défini par les documents**, pas rédigé librement :
toute demande de glissement (« tant qu'on y est… ») est traitée par cette
même règle d'exclusion.

### 2. Découper en tickets principaux (verticaux)

Un ticket principal par **fonctionnalité qui livre une valeur** :

- il incarne un ensemble **démontrable ou vérifiable seul** ;
- il tient dans **une semaine à dix jours** en équivalent temps/homme
  (au-delà, le scinder en plusieurs tickets principaux) ;
- il porte sa **justification métier** : section « Pourquoi » — la valeur
  ou le besoin client satisfait, du point de vue de qui en bénéficie. Un
  ticket sans justification n'est pas prêt à être créé ;
- il porte les **critères d'acceptation** du résultat d'ensemble, au
  format Given-When-Then (étant donné / quand / alors), testables sans
  jugement de valeur ;
- il porte le **hors-périmètre** de son lot : ce qui n'est pas fait dans
  ce ticket (écrit à partir de la confrontation étape 1).

Le découpage vertical est le **principe par défaut** : chaque ticket
traverse les couches nécessaires (données, API, interface, tests) et se
vérifie seul. Il n'est pas un absolu — voir l'étape 3 pour la réalité des
intervenants.

### 3. Découper en sous-tickets (horizontaux)

Quand la réalisation mobilise **plusieurs intervenants aux compétences
différentes**, le ticket principal se répartit en sous-tickets, par
compétence ou par zone. Ce sont des **étapes de réalisation et
d'intégration** de la fonctionnalité — pas des livrables autonomes.

- un sous-ticket dure **deux à quatre jours** au plus (au-delà, le diviser
  en sous-parties) ;
- la division reste sous la contrainte de validation : la **validation
  client porte sur le ticket principal**, jamais sur un sous-ticket ;
- les **dépendances** entre sous-tickets sont explicites : qui attend qui,
  et le **contrat d'interface** entre les lots (ce que chaque sous-ticket
  livre aux autres). Un découpage horizontal sans dépendances gérées est à
  proscrire ;
- la **frontière de travail** : les sous-tickets dont les prérequis sont
  satisfaits sont prenables en parallèle.

Exception — **refactor large** (changement impossible à maintenir verticalement,
ex. renommage massif) : découper en expand → migrate → contract. *expand*
bloque les lots de migration, *contract* est bloqué par tous ; si un lot ne
peut pas rester vérifiable seul, ajouter un ticket final « intégrer et
vérifier ».

### 4. Enrichir chaque ticket de son contexte de réalisation

Déterminer par la lecture du projet (pas par supposition) :

- les **fichiers et zones de code** concernés ;
- le **pattern existant** à suivre — la référence concrète (fichier,
  exemple), pas « suivez nos conventions » ;
- les **tests existants** du même type, à imiter ;
- les **commandes de vérification** exactes (tests, lint, typage) — jamais
  « s'assurer que ça marche ».

Un ticket doit être **exécutable sans question de clarification** : si
l'exécuteur (humain ou agent) doit demander des précisions, le ticket n'est
pas prêt. Vérifier avant de présenter : pas de « rapide », « bon UX »,
« s'assurer que » ; chaque critère est testable ; chaque référence pointe
vers quelque chose de réel.

### 5. Présenter la découpe et faire valider (avant toute création)

Rien ne part sur GitLab sans validation humaine (règle `pilotage-session`).
Présenter :

1. la **liste numérotée** des tickets principaux (titre, Pourquoi,
   critères d'acceptation, hors-périmètre) et, pour chacun, ses
   sous-tickets (titre, dépendances, contrat d'interface) ;
2. les **éventuels éléments hors périmètre** identifiés à l'étape 1.

Puis interroger sur : la **granularité** (faut-il fusionner ou scinder ?),
les **dépendances** (sont-elles réelles — « impossible de démarrer sans » —
ou seulement une préférence d'ordre ?), et la **justification métier**
(chaque Pourquoi est-il juste ?). Attendre l'accord explicite.

### 6. Créer les tickets sur GitLab

Après accord, créer dans l'ordre (les référencés en premier pour pouvoir
les citer) :

- **ticket principal** : issue GitLab avec titre, Pourquoi, critères
  d'acceptation, contexte de réalisation, hors-périmètre ;
- **sous-tickets** : sous-issues du ticket principal ;
- **dépendances** : relations de blocage GitLab (« is blocked by »), avec
  référence textuelle (« Bloqué par #N ») dans la description en secours ;
- **labels** : si le vocabulaire du board est déclaré dans
  `project-context.yaml` (`tickets.labels`), poser le label d'état initial ;
  sinon ne rien poser ;
- **milestone / poids** : renseigner seulement si l'information existe
  dans la demande ou les documents — jamais inventés ;
- **assignation** : proposer par sous-ticket d'après les compétences
  impliquées, appliquer seulement avec l'accord de l'utilisateur.

Rendre compte : les tickets créés (liens), les éléments hors périmètre
signalés, et ce qui reste à cadrer.

## Rappels

- **Ce qui n'est pas vendu n'est pas réalisé** : la règle d'exclusion est
  le garde-fou principal du découpage.
- **La validation client porte sur le ticket principal** : un sous-ticket
  n'est jamais présenté comme livrable.
- **Durées** : ≤ 10 jours/homme (principal), ≤ 4 jours (sous-ticket),
  sinon diviser — sans casser l'unité de validation.
- **Dépendances réelles seulement** : « je préfère faire A avant B » n'est
  pas un blocage.
- **Ne jamais inventer** : un contexte absent se demande, une référence
  manquante se signale.

---

## Sources d'inspiration (note d'entretien)

- mattpocock/skills — `to-tickets` / `to-issues` (tranches verticales,
  dépendances, validation avant publication, refactor large) ;
- alinaqi/ticket-craft (INVEST + exécutable sans clarification, critères
  Given-When-Then, contexte détecté, checklist) ;
- mattpocock/skills — `to-prd` (document d'origine, hors-périmètre).

Aucun contenu n'est repris tel quel : voir `01-synthese-brute.md` et
`02-amendements.md` dans `tmp/synthese-tickets-gitlab/` pour la traçabilité
complète (ce qui vient des sources, ce qui vient des choix du projet).
