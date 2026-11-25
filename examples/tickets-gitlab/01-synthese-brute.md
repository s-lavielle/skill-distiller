# Synthèse brute — skill « créer les tickets GitLab »

> Étape 1b du workflow de synthèse. Contenu : extraction fidèle des sources
> de la fiche `00-fiche-sources.yaml`, reformulée en français.
> Rien n'est inventé, rien n'est amendé : les ajouts personnels relèvent de
> l'étape 2 (document d'amendement).
> Chaque point est tracé à sa source par `[T]` (to-tickets), `[C]`
> (ticket-craft), `[P]` (to-prd).

## 1. Ce qu'est un ticket bien découpé

### 1.1 Tranches verticales (tracer bullets) [T]

Chaque ticket est une **tranche verticale** : un chemin étroit mais complet à
travers toutes les couches du changement (schéma de données, API, interface,
tests). Dès qu'il est livré, il est démontrable ou vérifiable **seul**.

À l'inverse, un **découpage horizontal** (une bille pour la base de données,
une pour l'API, une pour l'interface, une pour les tests) ne livre rien tant
que toutes les billes ne sont pas faites, et les critères d'acceptation de
chaque billes dépendent du travail des autres.

C'est la règle la plus souvent violée : face à une fonctionnalité transverse,
l'instinct est de couper par couche technique.

### 1.2 Taille et autonomie [T]

Chaque ticket doit tenir dans **un contexte de travail vierge** : une session
qui n'a jamais vu le document d'origine doit pouvoir le prendre et le livrer.
Un ticket qui contient plusieurs objectifs indépendants est trop grand.

### 1.3 Le quiz avant publication [T]

Rien ne part sur le tracker sans validation humaine. La découpe est présentée
sous forme d'une **liste numérotée**, et l'utilisateur est interrogé sur :

- la granularité est-elle la bonne ? faut-il fusionner ou scinder ?
- les liens de blocage sont-ils réels ?

C'est le moment de refuser, de fusionner, de scinder.

## 2. Dépendances entre tickets

### 2.1 Blocages réels [T]

Un lien « bloqué par » existe seulement si le ticket ne peut **pas démarrer,
ou ne peut pas rester correct tout seul**, sans l'autre. « Je préfère faire A
avant B » n'est pas un blocage : c'est une préférence d'ordre.

### 2.2 Frontière de travail [T]

Les tickets dont tous les bloqueurs sont résolus forment la **frontière** :
c'est l'ensemble du travail réellement prenable, en parallèle possible.
Des blocages déclarés à tort forcent une sérialisation inutile ; des blocages
oubliés font que deux travaux modifient en même temps un contrat encore
instable.

### 2.3 Exception : le refactor large [T]

Certains changements ne se prêtent pas aux tranches verticales — par exemple
renommer un champ partagé utilisé en milliers d'endroits, où aucun lot isolé
ne garde le système en état de passer. Le patron est alors **expand → migrate
→ contract** :

- *expand* : les deux formes coexistent, rien n'est cassé ;
- *migrate* : migration par lots, chaque lot garde la vérification au vert ;
- *contract* : suppression de l'ancienne forme, une fois la migration finie.

*expand* bloque les lots de migration ; *contract* est bloqué par tous.
Si un lot ne peut pas rester vert seul, on peut partager une branche
d'intégration et un ticket final « intégrer et vérifier ».

## 3. Contenu d'un ticket

### 3.1 Critères INVEST, plus « prêt pour l'agent » [C]

Un ticket doit satisfaire INVEST — indépendant, négociable, valuable,
estimable, small, testable — plus un critère supplémentaire : **exécutable
sans question de clarification**. Si l'exécuteur (humain ou agent) doit
demander des précisions, le ticket n'est pas prêt.

### 3.2 Types de tickets et gabarits [C]

Trois types courants, chacun avec son gabarit :

- **Fonctionnalité** : comportement attendu, contrat d'interface (requête /
  réponse / erreurs le cas échéant), critères d'acceptation ;
- **Bug** : comportement observé vs comportement attendu, reproduction,
  test de non-régression attendu ;
- **Dette technique** : ce qui est simplifié ou sécurisé, et ce qui devient
  possible ensuite.

### 3.3 Critères d'acceptation [C]

Au format **Given-When-Then** (étant donné / quand / alors) : une condition
initiale, une action, un résultat observable. Le test doit pouvoir en dire
« passe » ou « échoue », sans jugement de valeur.

### 3.4 Contexte détecté [C]

Le ticket enrichit la description de tout ce qui est déductible du projet
lui-même plutôt que de l'oublier :

- les fichiers et zones de code concernés ;
- le pattern existant à suivre (pas « suivez nos conventions » mais la
  référence concrète) ;
- les tests existants du même type, à imiter ;
- les **commandes de vérification** du projet (tests, lint, typage) — jamais
  « assurez-vous que ça marche » mais la commande exacte.

### 3.5 Hors-périmètre [P]

Chaque découpe porte une liste explicite de ce qui **n'est pas** fait dans ce
lot : c'est le garde-fou le plus efficace contre le glissement de périmètre
(« tant qu'on y est, on en profite pour… »).

### 3.6 Checklist de validation du ticket [C]

Avant de publier le ticket, vérifier que rien ne reste flou : pas de
« rapide », « bon UX », « s'assurer que » ; chaque critère est testable ;
chaque référence pointe vers quelque chose de réel ; les commandes de
vérification sont complètes.

## 4. Enchaînement avec la phase amont

### 4.1 Le document d'origine [P]

Les tickets découpent quelque chose : un plan, une spec, un PRD. Le document
d'origine fixe le problème, la solution, les comportements attendus (user
stories), les décisions arrêtées, et le **hors-périmètre**. Un découpage
sans document d'origine perd le fil de ce qui a été décidé.

---

## Signalements (à trancher à l'étape 2)

- **Ambiguïté de langue** : `ready-for-agent` [T] signifie « prêt à être
  exécuté par un agent sans triage supplémentaire » ; le critère « C » de
  [C] (« Claude-Ready ») recouvre la même idée sous un autre nom. Les deux
  notions se recouvrent : une seule règle suffira probablement.
- **Contradiction partielle** : [T] impose le quiz de validation humaine,
  [C] automatise la détection de contexte. Ce n'est pas contradictoire mais
  les deux se combinent : contexte auto-détecté + validation humaine du
  résultat.
- **Absence des sources** : rien sur GitLab spécifiquement (épics,
  milestones, poids, relations natives), ni sur le vocabulaire de labels du
  board, ni sur la justification métier des tickets. → étape 2.
- **Jargon à définir** : « tracer bullet », « frontière » (frontier),
  « expand/migrate/contract » — termes techniques des sources, à garder ou
  remplacer par des équivalents français selon le cadre posé à l'étape 2.
