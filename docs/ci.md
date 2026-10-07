# Intégration continue

Deux workflows GitHub Actions (`.github/workflows/`).

## Niveau 1 : `ci.yml` (sans accès à BigQuery)

Déclenché à chaque pull request et à chaque envoi sur `main`. Il compile les scripts Python, lance les tests du détecteur
d'anomalies et du cycle d'acquittement, puis `dbt parse` avec un profil factice (valide le YAML, les `ref()` et les macros).
Il n'utilise aucun secret, donc il tourne aussi pour les pull requests venant d'un fork.

## Niveau 2 : `dbt-build.yml` (avec BigQuery)

Déclenché à la main et chaque lundi à 06:00 UTC. Il s'authentifie par un compte de service (clé dans le secret `GCP_SA_KEY`),
lance `dbt build` (191 éléments) puis `monitoring/run_checks.py --fail`. Une alerte ouverte fait échouer le job ; GitHub envoie
un e-mail d'échec. Le rapport de santé apparaît dans le résumé du run.
Une alerte ouverte fait échouer le job. GitHub peut alors envoyer un e-mail d'échec ; cette notification n'a pas été testée.

## Pourquoi pas de build complet à chaque modification

Le projet utilise le sandbox BigQuery : 1 TiB de requêtes par mois et 10 GiB de stockage. Un build complet lit plusieurs Go
et réécrit les tables : à chaque commit, il épuiserait le quota. Le build écrit dans le même jeu de données que le
développement local (`dbt_dev`), pour ne pas dupliquer les tables.

## Secrets et accès

- `GCP_SA_KEY` (secret) : clé JSON d'un compte de service qui n'a que les rôles BigQuery Job User et BigQuery Data Editor.
- `GCP_PROJECT_ID` (variable) : identifiant du projet.
- La clé n'est jamais dans le dépôt ; le fichier local a été supprimé après dépôt dans le secret.
- Une fédération d'identité (Workload Identity Federation) évite de stocker une clé : amélioration possible.

## Limites

- Les tables `raw` ne sont pas reconstruites par la CI (elles viennent de fichiers Parquet locaux) ; elles expirent le 5 décembre 2026.
- Les dépendances ne sont pas épinglées : une nouvelle version peut casser le CI sans changement de code.
- Les tests dbt tournent sur les vraies données : pas de jeu de test réduit.
- Le niveau 2 n'est pas lancé automatiquement à chaque modification.