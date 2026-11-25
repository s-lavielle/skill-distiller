# Image de la CLI skill-distiller.
#
# Permet d'exécuter init/check/diff/new sur un projet cible monté en
# volume, sans installer Python sur l'hôte. Outre Python 3 (seule vraie
# dépendance de la CLI), l'image embarque git et curl : git pour les
# opérations sur le projet cible monté, curl pour le diagnostic réseau
# de `diff --fetch` (le téléchargement, lui, passe par urllib).
#
#   docker build -t skill-distiller .
#   docker run --rm -v <projet-cible>:/work skill-distiller init <sujet>

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# La CLI ne lit que bin/ et templates/ (ROOT = parent de bin), mais le
# dépôt complet reste utile dans l'image : tests/ pour les lancer dans
# le conteneur, docs/ et SKILL.md pour la procédure de distillation.
COPY . /opt/skill-distiller

# Raccourci dans le PATH : les commandes `docker compose exec` restent
# courtes (`skill-distiller init <sujet>`). Path.resolve() du script
# remonte le lien vers /opt/skill-distiller : ROOT et templates/ sont
# trouvés au bon endroit.
RUN ln -s /opt/skill-distiller/bin/skill-distiller /usr/local/bin/skill-distiller

# Les commandes s'exécutent depuis la racine du projet cible : c'est le
# répertoire de travail par défaut du conteneur (/work, monté en volume).
WORKDIR /work

# Entrypoint CLI : `docker run` s'utilise en usage ponctuel. Le compose
# le surcharge (sleep infinity) pour le modèle conteneur longue durée +
# exec.
ENTRYPOINT ["skill-distiller"]
CMD ["--help"]
