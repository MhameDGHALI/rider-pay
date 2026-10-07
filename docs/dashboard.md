# Tableau de bord Power BI

Fichier : `dashboards/rider_pay.pbix`. Mode Import. Source : BigQuery, tables agrégées de la couche marts, du monitoring et du simulateur.

## Modèle

| Table | Dataset | Rôle |
|---|---|---|
| dim_date, dim_operator, dim_zone | dbt_dev_marts | Dimensions |
| agg_daily_operator | dbt_dev_marts | Courses, rémunération, tarif par jour et opérateur |
| agg_zone_hour, agg_zone_congestion | dbt_dev_marts | Agrégats par zone (sans date ni opérateur) |
| dq_daily_metrics | dbt_dev_monitoring | Santé des données |
| sim_scenario_comparison, sim_scenario_rule_bonus, sim_snow_sensitivity | dbt_dev_simulation | Simulateur |
| incidents_acquittes | CSV du dépôt (`monitoring/acknowledged_alerts.csv`) | Registre des incidents |

`fct_trips` (12,2 M de lignes) n'est pas importée : les agrégats suffisent. 7 relations, [N] mesures.

## Pages

1. **Trip Economics** 
2. **Incentive Simulator** 
3. **Data quality**

## Principes

- Les ratios sont recalculés par des mesures DAX à partir des sommes ; les colonnes de ratios pré-calculés sont masquées.
- Toute analyse de rémunération porte sur les courses propres (`is_clean_trip`).
- Les mesures du simulateur sont gardées : sans scénario unique, elles renvoient une valeur vide plutôt qu'une somme.
- Un jaune unique signale ce qui est à lire avec prudence (incidents, hypothèses, limites).

## Comment ouvrir le rapport

1. Installer Power BI Desktop (Windows, gratuit).
2. Ouvrir `dashboards/rider_pay.pbix` : les données sont dans le fichier.
3. Ne pas actualiser sans reconstruire les tables BigQuery (`dbt build`) : elles expirent après 60 jours dans le sandbox.

## Limites

- Les segmenteurs Opérateur et Mois ne filtrent pas les visuels de zones : ces agrégats n'ont ni opérateur ni date.
- Le coût du simulateur est statique ; ses règles sont des hypothèses ; les montants sont à l'échelle de l'échantillon de 30 %.
- « Rémunération par heure de course » est la rémunération divisée par la durée des courses, pas un salaire horaire.
- « Part plateforme » est approximative (le tarif de base exclut taxes et frais).
- Le registre des incidents est chargé depuis un chemin local : le fichier affiche les données mises en cache mais ne peut pas les actualiser sur un autre poste.

## Version

Rapport figé le [date].