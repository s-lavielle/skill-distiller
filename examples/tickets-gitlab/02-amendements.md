# Document d'amendement — skill « créer les tickets GitLab »

> Étape 2a du workflow de synthèse. Ce document amende globalement la
> synthèse brute (`01-synthese-brute.md`) : ajouts, amendements, cadre.
> Tout ce qui figure ici est un choix de l'utilisateur, distinct de ce que
> disent les sources.

## Ajouts

### A6 — GitLab spécifiquement

Les sources sont tracker-agnostic ; le skill cible GitLab. Choix retenus
(propositions à valider) :

- **Sous-issues natives** : les sous-tickets (A2) sont créés en
  sous-issues GitLab du ticket principal. La structure du modèle A2 est
  ainsi directement représentée dans le tracker.
- **Relations de blocage natives** : les dépendances entre tickets (et
  entre sous-tickets) utilisent les relations d'issue GitLab (« is
  blocked by »), avec référence textuelle dans la description en secours
  (« Bloqué par #N ») pour rester lisible sans passer par l'API.
- **Épics** : non retenu pour l'instant. Le ticket principal est une
  issue parente (avec sous-issues), pas un epic. À revoir si le modèle
  A2 monte en échelle.
- **Milestones et poids** : renseignés si l'information existe dans la
  demande ou les documents de référence ; jamais inventés, laissés vides
  sinon.
- **Labels** : si le vocabulaire du board est déclaré dans
  `project-context.yaml` (`tickets.labels`), appliquer le label d'état
  initial (ex. « à faire ») à la création. Sinon, ne rien poser.
- **Assignation** : proposer un assigné par sous-ticket d'après les
  compétences impliquées ; ne jamais assigner sans accord explicite.

### A7 — Justification métier des tickets

Aucune source ne l'exige ; la règle interne `pourquoi` du projet l'impose
pour les commits et les tests. Extension aux tickets :

- Chaque **ticket principal** porte une section **« Pourquoi »** : la
  valeur métier ou le besoin client qu'il satisfait, formulé du point de
  vue de qui en bénéficie.
- Un ticket sans justification explicite n'est pas prêt à être créé.

## Amendements

### A1 — Tranches verticales : principe, pas absolu

- **Cible** : §1.1 « Tranches verticales (tracer bullets) ».
- **Contenu** : le découpage vertical reste le principe par défaut, mais il
  se heurte à une réalité d'équipe : plusieurs intervenants aux
  compétences différentes, et un ticket qui doit passer de l'un à l'autre
  avec des limites parfois floues. Un cadrage **horizontal** (par
  compétence ou par zone) est parfois nécessaire et légitime.
- **Conséquence** : quand le découpage est horizontal, l'exigence se
  reporte sur la **gestion des dépendances entre les tâches** : liens
  explicites (qui attend qui), contrat d'interface entre les lots (ce que
  chaque lot livre aux autres), et cohérence de l'ensemble. Le
  découpage horizontal sans gestion de dépendances reste à proscrire.
- **Articulation** : voir A2 — le ticket principal reste vertical ; le
  horizontal s'exprime en sous-tickets à l'intérieur.

### A2 — Ticket principal vertical, découpage horizontal en sous-tickets

- **Contenu** : la structure de référence est à deux niveaux.
  - Le **ticket principal** est une unité **verticale** : il représente un
    ensemble qui livre une valeur, se démontre ou se vérifie seul.
  - Sa **répartition horizontale** se fait en **sous-tickets (ou
    sous-tâches)**, typiquement par compétence ou par zone : le travail
    interne de réalisation, réparti entre les intervenants.
- **Conséquence** : les dépendances entre sous-tickets (qui attend qui,
  contrat d'interface) se gèrent **dans le périmètre du ticket principal** ;
  la livraison et la vérification restent au niveau du ticket principal.
  C'est le ticket principal qui porte les critères d'acceptation du
  résultat d'ensemble.

### A3 — La validation client porte sur le ticket principal

- **Contenu** : ce qui est **validé par le client**, c'est le ticket
  principal — l'unité verticale qui incarne la fonctionnalité. Les
  sous-tickets ne sont que des **étapes de réalisation/intégration** de
  cette fonctionnalité : ils n'ont pas de valeur de validation
  indépendante.
- **Conséquence** : la vie d'un sous-ticket (terminé, en cours) n'a de
  sens que rapportée au ticket principal ; c'est le principal qui passe
  en validation, et c'est sur lui que porte l'accord du client. Un
  sous-ticket isolé ne se présente jamais comme livrable à valider.

### A4 — Durées maximales : 1 à 10 jours pour le principal, 2 à 4 jours pour un sous-ticket

- **Cible** : §1.2 « Taille et autonomie ».
- **Contenu** : dans la mesure du possible,
  - un ticket **vertical (principal)** ne doit pas durer plus d'une
    **semaine à dix jours** en équivalent temps/homme ;
  - un **sous-ticket (horizontal)** ne doit pas durer plus de **deux à
    quatre jours**.
- **Conséquence** : au-delà, le ticket ou le sous-ticket doit être
  **divisé en sous-parties**. La division reste sous la contrainte de A3 :
  les sous-parties restent des étapes d'intégration du ticket principal,
  dont la validation par le client porte sur le principal — pas de
  sous-partie qui deviendrait un livrable client autonome.

### A5 — Documents de référence : ce qui a été vendu fait foi

- **Cible** : §4.1 « Le document d'origine ».
- **Contenu** : lors du découpage, se référer à un ou plusieurs documents
  de **ce qui a été vendu** :
  - le **cahier des charges initial** ;
  - la **proposition commerciale et technique**, dans la mesure où elle
    précise des points : clarifications, options (retenues ou non
    retenues) ;
  - les **avenants**, partie technique et commerciale.
- **Règle d'exclusion** : toute fonctionnalité demandée et/ou spécifiée
  **qui n'est pas référencée dans ces documents** est considérée comme
  **hors périmètre**. Elle ne figure dans aucun ticket de la découpe sans
  avoir été au préalable identifiée comme telle et traitée comme un
  ajout (avenant, validation explicite) — pas de glissement « tant qu'on
  y est ».
- **Accès aux documents** : ces documents doivent être disponibles via un
  **point d'accès unique à définir** (emplacement à identifier — chemin,
  URL, espace documentaire). Ils ne sont pas nécessairement référencés
  dans chaque ticket : c'est le point d'accès qui les rend disponibles
  au découpeur comme à l'exécuteur. → point ouvert : où ce point
  d'accès est-il déclaré (contexte projet ? lien dans la convention du
  projet ?) — à trancher avant rédaction du skill.
- **Source dans la session** : ces informations (point d'accès aux
  documents de référence) doivent figurer dans le **contexte de la
  session** qui utilise le skill. Si elles n'y sont pas, le skill **les
  demande à l'utilisateur** avant de découper — jamais supposées, jamais
  inventées.

## Cadre

- **Langue** : français (champ de la fiche de sources, défaut).
- **Ton** : direct, factuel, sans jargon d'outil. Vocabulaire du projet
  et du métier, pas celui des sources anglophones (sauf terme technique
  utile, alors défini à sa première occurrence).
- **Conventions à respecter** : `perimetre-projet` (un projet, un sujet
  par session), `pilotage-session` (validation humaine avant toute
  action engageante — ici la création des tickets), `style-doc`
  (lisibilité), `pourquoi` (chaque règle du skill est justifiée),
  `fichiers-echange` (les artefacts de fabrication restent dans `tmp/`).
- **Traçabilité** : le skill est **autonome** dans son corps (utilisable
  sans lire les sources) ; une note de fin de fichier nomme les sources
  d'inspiration, pour l'entretien futur du skill.
- **Structure** : format des skills du projet — front-matter `name` /
  `description`, déroulé numéroté, rappels en fin.
