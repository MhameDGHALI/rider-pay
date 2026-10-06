# Seuil de rentabilité et règle de décision

Bonus c = 1.50 $ par course, marge moyenne m = 6.25 $ par course (tarif de base moins rémunération, approximative).
Seuil de rentabilité : L* = c / (m - c) = 31.6 % de courses en plus.

## Coût du bonus par course supplémentaire

| hausse du nombre de courses (%) | coût du bonus par course supplémentaire ($) |
|---|---|
| 2.5 | 61.5 |
| 5.0 | 31.5 |
| 10.0 | 16.5 |
| 15.0 | 11.5 |
| 20.0 | 9.0 |
| 25.0 | 7.5 |
| 30.0 | 6.5 |
| 31.6 | 6.25 |
| 40.0 | 5.25 |
| 50.0 | 4.5 |

## Règle de décision appliquée aux effets injectés (répartition réelle)

| analyse | effet vrai (%) | effet estimé (%) | IC 95 % bas (%) | IC 95 % haut (%) | décision | bonne décision | verdict |
|---|---|---|---|---|---|---|---|
| Principale (toutes les unités) | 0 | 10.0 | -0.8 | 21.9 | abandonner | abandonner | correcte |
| Principale (toutes les unités) | 5 | 15.5 | 4.2 | 28.0 | abandonner | abandonner | correcte |
| Principale (toutes les unités) | 15 | 26.5 | 14.1 | 40.1 | non concluant | abandonner | non concluant |
| Principale (toutes les unités) | 25 | 37.5 | 24.1 | 52.3 | non concluant | abandonner | non concluant |
| Sensibilité (sans jours perturbés, exploratoire) | 0 | 1.6 | -2.2 | 5.6 | abandonner | abandonner | correcte |
| Sensibilité (sans jours perturbés, exploratoire) | 5 | 6.7 | 2.7 | 10.8 | abandonner | abandonner | correcte |
| Sensibilité (sans jours perturbés, exploratoire) | 15 | 16.9 | 12.5 | 21.4 | abandonner | abandonner | correcte |
| Sensibilité (sans jours perturbés, exploratoire) | 25 | 27.0 | 22.3 | 32.0 | non concluant | abandonner | non concluant |

## Probabilité de chaque décision : Principale (toutes les unités)

| effet vrai (%) | abandonner (%) | non concluant (%) | adopter (%) |
|---|---|---|---|
| 0.0 | 100.0 | 0.0 | 0.0 |
| 10.0 | 92.1 | 7.9 | 0.0 |
| 20.0 | 40.6 | 59.4 | 0.0 |
| 30.0 | 4.1 | 95.0 | 0.9 |
| 40.0 | 0.0 | 78.8 | 21.2 |
| 50.0 | 0.0 | 32.9 | 67.1 |
| 60.0 | 0.0 | 3.5 | 96.5 |
| 70.0 | 0.0 | 0.0 | 100.0 |

## Probabilité de chaque décision : Sensibilité (sans jours perturbés, exploratoire)

| effet vrai (%) | abandonner (%) | non concluant (%) | adopter (%) |
|---|---|---|---|
| 0.0 | 100.0 | 0.0 | 0.0 |
| 10.0 | 100.0 | 0.0 | 0.0 |
| 20.0 | 99.9 | 0.1 | 0.0 |
| 30.0 | 9.0 | 90.6 | 0.4 |
| 40.0 | 0.0 | 8.5 | 91.5 |
| 50.0 | 0.0 | 0.0 | 100.0 |
| 60.0 | 0.0 | 0.0 | 100.0 |
| 70.0 | 0.0 | 0.0 | 100.0 |
