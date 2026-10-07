# Tableau de bord Power BI

Fichier : `dashboards/rider_pay.pbix`. Mode Import. Source : BigQuery, tables agrégées de la couche marts et du monitoring.

## Modèle

| Table | Dataset | Rôle |
|---|---|---|
| dim_date, dim_operator, dim_zone | dbt_dev_marts | Dimensions |
| agg_daily_operator | dbt_dev_marts | Courses, rémunération, tarif par jour et opérateur |
| agg_zone_hour, agg_zone_congestion | dbt_dev_marts | Agrégats par zone (sans date ni opérateur) |
| dq_daily_metrics | dbt_dev_monitoring | Santé des données (page 3, jour 20) |
| sim_* (3 tables) | dbt_dev_simulation | Simulateur (page 2, jour 20) |

`fct_trips` (12,2 M de lignes) n'est pas importée : les agrégats suffisent.

## Principes

- Les ratios sont recalculés par des mesures DAX à partir des sommes ; les colonnes de ratios pré-calculés sont masquées.
- Toute analyse de rémunération porte sur les courses propres (`is_clean_trip`).
- Chaque chiffre est réconcilié avec BigQuery (`docs/bi_reconciliation.md`).

## Limites

- Les filtres Opérateur et Mois ne s'appliquent pas aux visuels de zones : ces agrégats n'ont ni opérateur ni date.
- « Rémunération par heure de course » est la rémunération divisée par la durée des courses, pas un salaire horaire.
- « Part plateforme » est approximative (le tarif de base exclut taxes et frais).
- Données de l'échantillon de 30 % : les montants absolus ne représentent pas la réalité, les moyennes et ratios restent valables.