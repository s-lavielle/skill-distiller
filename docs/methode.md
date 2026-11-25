# La méthode — distiller un skill, pas le copier

> Pourquoi `skill-distiller` existe, et pourquoi le mot *distillation*.
> Pour le détail des références, voir [`etat-de-l-art.md`](etat-de-l-art.md).

## Thèse — la réutilisation par copie

Des centaines de skills existent déjà, dans des dépôts publics ou
internes. Face à un besoin de skill, la tentation naturelle est la
copie : prendre un skill existant, le déposer dans son projet, l'activer.
C'est rapide, et le skill « marche » souvent dès le premier essai.

## Antithèse — ce que la copie ne donne pas

Un skill copié est une **boîte noire** :

- on ne sait pas d'où viennent ses règles, lesquelles sont essentielles
  et lesquelles ne concernent que le projet d'origine ;
- sa langue, son ton et ses conventions ne sont pas ceux du projet cible ;
- ses spécificités d'outil (l'agent, la plateforme, l'ancien projet) y
  sont brodées dedans ;
- il évolue sans nous : sans traçabilité, aucune mise à jour ni
  vérification n'est possible.

Un skill qu'on ne maîtrise pas ne devrait pas être exécuté par un agent.

## Synthèse — la distillation

Entre la copie et la réécriture from scratch : la **distillation**. On lit
les sources comme une **inspiration**, on en extrait la substance, on
arbitre entre les sources, on y ajoute ses propres règles, et on rédige un
skill **nouveau, autonome et maîtrisé**.

Deux registres restent séparés jusqu'à la rédaction finale :

- **la synthèse** — ce que disent les sources, reformulé dans la langue
  cible, chaque point tracé à sa source ;
- **l'amendement** — les choix de l'utilisateur, explicites et datés.

Le skill final les fusionne : chaque règle est tracée, soit à une source,
soit à un choix explicite. D'où le sous-titre du produit : **auditable
skill synthesis**. Le déroulé complet — fiche de sources, synthèse brute,
réconciliation, amendements, skill final — est dans [`../SKILL.md`](../SKILL.md).

## Pourquoi « distillation »

Distillation au sens **alchimique** : affiner des matières brutes en un
produit nouveau, plus pur, maîtrisé de bout en bout — pas la simple
décantation, et surtout pas la copie.

⚠️ **À ne pas confondre** : la littérature de recherche emploie aussi
« distillation » (ou *skill synthesis*) pour l'extraction de skills
depuis des **trajectoires d'exécution** d'agents (*trajectory mining*,
ex. AutoSkill). skill-distiller fait autre chose : sa matière première est
**écrite** — skills existants, documentations, articles — et son produit
est un artefact rédigé et auditable, pas un condensé de traces
d'exécution.

## Place dans le paysage

Le survey *A Systematic Survey of Agentic Skills* (arXiv 2608.29596,
§3.5) trace la ligne de démarcation :

- **composition** — orchestrer plusieurs skills à l'exécution ;
- **synthesis** — produire un **nouvel artefact** à partir de plusieurs
  apports.

skill-distiller est du côté **synthesis** : il produit un skill neuf,
tracé, rédigé dans les conventions du projet cible. Ses voisins directs —
SkillFusion, Skill-Synthesizer, SkillGen, Frankenstein — sont détaillés
dans [`etat-de-l-art.md`](etat-de-l-art.md) ; la différence tient en un
point : chez nous, **l'humain arbitre à chaque étape**.

## Le processus s'amende lui-même

Ce qui a manqué pendant une exécution est intégré au workflow : la
réconciliation des sources multiples, par exemple, a été ajoutée après
coup, à l'usage. C'est ce qui rend la méthode réutilisable — et ce
document reste ouvert à ses propres amendements.

## Le cycle de vie : créer, puis faire évoluer

Une distillation n'est pas à sens unique. Les sources bougent, et le
skill distillé dérive en silence si personne ne regarde. La
**réintégration** (voir `SKILL.md`) prolonge le cycle : les sources sont
**figées** à la lecture (copie conservée dans le lot), `skill-distiller
diff` compare la copie figée à la source actuelle, et le processus est
refait **sur les seuls changements** — synthèse des nouveautés, arbitrage
humain, skill final vN avec note de sources datée.

Mémoire du lot : tout est conservé (artefacts, sources figées, cycles de
réintégration) mais rien n'est versionné — **la solution est versionnée
dans un dépôt, pas ses produits**.
