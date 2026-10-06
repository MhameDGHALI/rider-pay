# Surveillance de la qualité des données

## Principe

- Un modèle dbt (`dq_daily_metrics`) calcule 6 indicateurs par jour et par opérateur.
- Un détecteur (`monitoring/detect.py`) compare chaque jour aux autres jours de même type (même opérateur, même jour de
  la semaine) avec un score robuste (médiane et écart absolu médian), seuil 4.
- Un événement attendu (jour férié, forte neige, lendemain), déduit du calendrier et de la météo, explique les variations de
  la demande : ces anomalies sont des informations. La qualité des données (part de courses signalées, chronologies
  incohérentes) reste une alerte même un jour de tempête.
- Une alerte examinée est acquittée dans `monitoring/acknowledged_alerts.csv` avec sa raison : elle reste dans le rapport.

## Incidents examinés

## Incidents examinés

| Jour | Opérateur | Constat | Raison de l'acquittement |
|---|---|---|---|
| 22 janvier | Lyft | 9,5 % de courses signalées (5 241 sur 55 246), 99,6 % pour tarif de base nul ou négatif ; 99,6 % d'entre elles à partir de 19h (10 % à 19h, 39 à 47 % de 20h à 23h) | Défaut de tarif de base, cause non établie ; courses exclues des analyses par `is_clean_trip` |
| 23 janvier | Lyft | 10,2 % de courses signalées (6 905 sur 68 004), 99,7 % pour tarif nul ou négatif : même défaut que la veille | Idem |
| 25 janvier | Uber | 24,2 % de courses signalées (17 072 sur 70 463) : 98,5 % pour tarif nul ou négatif, 88,5 % pour rémunération nulle, 17 rémunérations négatives ; jour de forte neige (18,9 cm) | Cause non établie ; la tempête explique la baisse de volume, pas les tarifs et rémunérations nuls ; courses exclues par `is_clean_trip` |

**Concentration.** Ces trois journées représentent 1,6 % des courses et **83,3 % des 35 087 courses signalées**
(48,7 % pour Uber le 25 janvier, 19,7 % et 14,9 % pour Lyft les 23 et 22 janvier). Hors de ces journées, la part de courses
signalées est d'environ 0,05 %. Le 25 janvier concentre aussi 93 % des courses à rémunération nulle du projet.

**Effet sur les analyses.** Le filtre `is_clean_trip` exclut ces courses des analyses de rémunération, de marge et d'expérimentation.
L'écart de rémunération sous la neige observé au jour 7 venait en grande partie de la journée du 25 janvier chez Uber, qui est à la fois
une journée de forte neige et un incident de données : la neige et l'incident coïncident, rien ne montre que l'un cause l'autre.

## Sensibilité du détecteur

[Recopier le tableau de docs/detector_evaluation.md et, pour chaque indicateur, la plus petite taille détectée à 80 %.]

## Validation

- `monitoring/test_detect.py` : séries simulées, anomalies injectées une par une, série saine, événement attendu,
  qualité un jour de tempête.
- `monitoring/test_alerting.py` : acquittement, message, journal périmé.
- `monitoring/evaluate_detector.py` : sensibilité sur les vraies données.

## Limites

- 59 jours d'historique : le « normal » repose sur 7 à 8 jours comparables.
- La référence est construite sur la même période : une dérive lente qui toucherait tous les jours est invisible.
- Un seul jour est testé à la fois ; les plus petites anomalies sont sous les planchers d'échelle.
- Le seuil (4) a été calibré sur des séries simulées ; les vraies données ont des queues plus lourdes.
- L'envoi par webhook n'a pas été testé.