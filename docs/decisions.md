# Journal de décisions

Chaque ligne indique ce qui a été décidé, pourquoi, et ce qui a été écarté.
Les décisions marquées « à confirmer » reposent sur une hypothèse que je n'ai pas encore vérifiée.

## Décisions

| # | Jour | Décision | Pourquoi | Alternative écartée |
|---|---|---|---|---|
| 1 | 1 | Échantillon aléatoire de 30 % des courses (graine 42) | Les deux mois pèsent environ 40,8 M de lignes, trop pour les 10 Go du sandbox BigQuery. À 30 %, il reste 12 244 353 courses. Les écarts avec les fichiers complets sont inférieurs à 0,1 % sur les moyennes, et la graine rend l'échantillon reproductible. | Charger toutes les courses (dépasse le sandbox) ; un seul mois ; un tirage sans graine (non reproductible) |
| 2 | 2 | Table brute non partitionnée par date, seulement clusterisée par opérateur et zone de départ | Le sandbox supprime les partitions 60 jours après leur date. Les courses datent de janvier-février 2026 : des partitions par date risquaient d'être supprimées au chargement. | Partitionner `pickup_datetime` par jour (risque de perte de données) |
| 3 | 4 | Conversion TIMESTAMP vers DATETIME sans fuseau horaire | Les heures TLC sont locales (New York), sans fuseau. BigQuery les a typées TIMESTAMP (UTC) au chargement, mais les chiffres sont justes. `DATETIME(x)` les conserve ; avec `'America/New_York'`, toutes les heures seraient décalées de 5 heures et la jointure avec la météo serait fausse sans aucune erreur. | Convertir avec un fuseau ; recharger la table brute en DATETIME (la couche brute doit rester fidèle à ce qui a été chargé) |
| 4 | 3 | Zones TLC chargées comme seed dbt, avec `N/A` remplacé par `Unknown` | Petit fichier de référence (265 lignes) versionné dans le dépôt. Les valeurs `N/A` des zones 264 et 265 sont ambiguës : après normalisation, les tests `not_null` et `accepted_values` sont fiables. | Charger les zones par script dans `raw` ; garder `N/A` tel quel |
| 5 | 3-4 | Staging fidèle : aucune ligne supprimée, les anomalies sont signalées plus tard | Le staging copie la source en renommant et en typant. Filtrer à ce niveau perdrait de l'information de façon irréversible et fausserait les réconciliations. La logique métier est dans la couche intermediate. | Supprimer les courses anormales dès le staging |
| 6 | 4 | Tests en `error` ou en `warn` selon la gravité | Une erreur bloque quand la table est inutilisable (clé dupliquée, heure de prise en charge vide). Un avertissement signale une anomalie à examiner sans bloquer : les 21
| 24 | 11 | Règles de bonus et scénarios écrits dans des seeds | | |
| 25 | 11 | Simulation sur des segments (768 lignes au plus) plutôt que sur 12 M de courses | | |
| 26 | 11 | Règles d'un scénario cumulées, bonus en pourcentage appliqués à la rémunération réelle | | |
| 27 | 11 | Coût statique : aucune réaction du comportement des chauffeurs | | |
| 28 | 11 | Règles de bonus = hypothèses, rémunération de base = donnée réelle | | |