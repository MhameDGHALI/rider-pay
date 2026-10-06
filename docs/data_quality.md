# Rapport de qualité des données

Périmètre : 12 244 353 courses (échantillon aléatoire de 30 %, janvier-février 2026).

## Chaîne de réconciliation

Chaque passage d'une couche à l'autre est contrôlé par un test dbt qui compare le nombre de lignes
et au moins un total financier.

| De | Vers | Contrôle | Test |
|---|---|---|---|
| `raw.hvfhv_trips` | `stg_hvfhv_trips` | lignes, somme de `driver_pay` | `assert_trips_reconcile_with_raw` |
| `stg_hvfhv_trips` | `int_trip_economics` | lignes, somme de `driver_pay` | `assert_int_trip_economics_reconcile_with_staging` |
| `int_trip_economics` | `int_trips_enriched` | lignes, somme de `driver_pay` | `assert_int_trips_enriched_reconcile_with_economics` |
| `int_trips_enriched` | `fct_trips` | lignes, 3 sommes (rémunération, tarif, pourboires) | `assert_fct_trips_reconcile_with_enriched` |
| `fct_trips` | 3 agrégats | lignes, courses propres, courses avec frais, rémunération | `assert_agg_*_reconciles_with_fct` |
| `raw.hvfhv_trips` | faits et agrégats | bout en bout : lignes, frais, rémunération | `assert_end_to_end_raw_to_aggregates` |

Résultat : 12 244 353 courses, 12 209 266 courses propres et 3 855 997 courses avec frais de congestion
sont retrouvées à l'identique dans chaque couche.

## Anomalies repérées

Aucune ligne n'est supprimée : les anomalies sont signalées par des indicateurs (`has_*`, `is_clean_trip`).

| Anomalie | Courses | Part |
|---|---|---|
| Rémunération négative | 21 | 0,0002 % |
| Rémunération nulle | 16 187 | 0,13 % |
| Tarif de base nul ou négatif | 31 544 | 0,26 % |
| Distance nulle ou négative | 1 446 | 0,012 % |
| Durée nulle ou négative | 290 | 0,0024 % |
| Durée incohérente avec les horodatages | 1 528 | 0,012 % |
| **Courses signalées (union des six)** | **35 087** | **0,29 %** |
| Chronologie incohérente | 222 478 | 1,82 % |

Les six premières catégories se recoupent fortement : l'union (35 087) dépasse de seulement 3 543 courses
la plus grande catégorie (31 544).

### Chronologie incohérente
- Pour 164 284 courses (1,34 %), l'heure de la demande est postérieure à la prise en charge.
- L'heure d'arrivée du chauffeur est postérieure à la prise en charge pour 397 courses seulement (0,003 %).
- Le champ en cause est donc surtout `request_datetime`. Le dictionnaire TLC ne réserve `on_scene_datetime`
  qu'aux véhicules accessibles, mais le champ est rempli pour toutes les courses.
- Règle : les analyses d'attente filtrent sur `NOT has_timeline_anomaly` et utilisent la médiane.

### Effet des anomalies sur une analyse
- Les 21 rémunérations négatives : 17 se concentrent le dimanche 25 janvier 2026, toutes chez Uber.
- Les courses signalées représentent 2,41 % des courses des heures de neige, contre 0,17 % hors neige.
- Écart de rémunération moyenne sous la neige : environ -0,7 $ sur toutes les courses, -0,21 $ (-1,0 %)
  sur les courses propres.

## Contrôles croisés
- Zone aéroport (fichier de zones) contre frais d'aéroport (facturation) : concordance de 99,8 %
  (22 598 désaccords sur 12 244 353).
- Frais de congestion : 31,5 % des courses le paient. 38 zones de départ, toutes à Manhattan, le paient
  dans plus de 95 % des cas (règle empirique, pas la définition officielle de la zone).

## Représentativité de l'échantillon
Écarts inférieurs à 0,1 % sur les moyennes (rémunération, distance, part d'Uber, part plateforme)
et inférieurs à 0,03 point sur la répartition par quartier.

## Cas non résolus
- Cause de la concentration des anomalies de rémunération le 25 janvier : non établie.
- Cause des demandes postérieures à la prise en charge : non établie.
- 22 598 désaccords entre zone aéroport et frais d'aéroport : non expliqués.