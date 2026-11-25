# Exemple de greffon de conventions locales

> Comment un projet cible **greffe ses propres conventions** sur le
> workflow : ces choix remplissent la section « Cadre » de l'étape 4
> (amendements) et encadrent la rédaction du skill final (étape 5). Copier
> ce fichier dans le projet cible et l'adapter — c'est un exemple, pas un
> standard.

## Langue et ton

- Langue cible : <français par défaut ; autre langue le cas échéant>.
- Ton : <directif / tutoriel / référence…>, phrases courtes.

## Répertoire de travail

- Par défaut : `threads/<sujet>/` (jamais versionné).
- Surcharge : <nom du répertoire si le projet en impose un autre, ex.
  `atelier/`> — à déclarer ici et dans le `.gitignore` du projet.

## Traçabilité

- Le skill final cite-t-il ses sources ? <oui — note de sources en fin /
  non> ;
- Les règles non évidentes sont-elles justifiées ? <oui / non>.

## Structure du skill final

- Format : <front-matter `name` / `description`, déroulé numéroté,
  rappels en fin — ou le format du projet cible> ;
- Emplacement d'installation : <répertoire de skills du projet>.

## Périmètre

- Le skill produit vise : <le projet X / l'équipe Y>.
- Un sujet qui vise un autre projet est signalé, pas traité en douce.
