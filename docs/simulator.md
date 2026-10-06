# Simulateur d'incitations

## À quoi ça sert

Estimer le coût de règles de bonus de rémunération sur les courses d'un échantillon, et comparer des scénarios.
Les règles sont des **hypothèses** de travail. La rémunération de base (`driver_pay`) est une donnée réelle.
Le coût calculé est **statique** : on suppose que les chauffeurs se comportent comme avant.
Il chiffre ce que coûterait un bonus ; il ne dit pas s'il fonctionne. Cette question relève de l'analyse A/B.

## Comment ça marche

```
fct_trips (courses propres)
     |
sim_trip_segments (731 segments)
     |
sim_rules + sim_scenario_rules --> sim_scenario_segment_bonus --> sim_scenario_comparison
                               \-> sim_scenario_rule_bonus      (coût de chaque règle)
                               \-> sim_snow_sensitivity         (balayage du taux de neige)
```

1. Les courses propres sont regroupées en 731 segments (opérateur, neige, heure, semaine ou week-end,
   zone à frais élevé, aéroport). Un segment porte un nombre de courses et des sommes, donc des valeurs additives.
2. Chaque règle (seed `sim_rules`) a des conditions et un montant : un pourcentage de la rémunération
   ou un montant fixe par course.
3. Un scénario (seed `sim_scenarios`) cumule les règles qui lui sont rattachées (seed `sim_scenario_rules`).
4. Le coût d'une règle sur un segment vaut `taux x rémunération du segment` ou `montant x nombre de courses`.
5. Les macros `sim_rule_matches` et `sim_bonus_amount` portent cette logique. Elles sont réutilisées par le calcul
   des scénarios, la décomposition par règle et l'analyse de sensibilité.

## Les règles et les scénarios

| Règle | Description (hypothèse) |
|---|---|
| `R_SNOW_15` | +15 % de la rémunération pendant les heures de neige |
| `R_SNOW_165` | +16,5 % de la rémunération pendant les heures de neige |
| `R_PEAK_AM` | +1,50 $ par course en semaine, de 8h00 à 9h59 |
| `R_PEAK_PM` | +1,50 $ par course en semaine, de 16h00 à 21h59 |
| `R_ZONE_100` | +1,00 $ par course au départ d'une zone à frais de congestion élevé |

| Scénario | Règles |
|---|---|
| `BASE` | Aucune : la situation actuelle |
| `SNOW_15` | `R_SNOW_15` |
| `SNOW_165` | `R_SNOW_165` (le bonus neige augmenté de 10 %) |
| `PEAK_150` | `R_PEAK_AM` et `R_PEAK_PM` |
| `ZONE_100` | `R_ZONE_100` |
| `COMBINED` | `R_SNOW_15`, `R_PEAK_AM`, `R_PEAK_PM` et `R_ZONE_100` |

Une zone « à frais élevé » est une règle empirique : au moins 100 courses et au moins 95 % de courses
avec frais de congestion. Ce n'est pas la définition officielle de la zone.

## Ajouter un scénario

1. Ajouter la règle dans `seeds/sim_rules.csv` (conditions, type de bonus, valeur).
2. Ajouter le scénario dans `seeds/sim_scenarios.csv`.
3. Rattacher la règle au scénario dans `seeds/sim_scenario_rules.csv`.
4. Lancer :
```
   dbt seed --select sim_scenarios sim_rules sim_scenario_rules
   dbt build --select sim_scenario_segment_bonus sim_scenario_comparison sim_scenario_rule_bonus sim_snow_sensitivity
```

Les tests des seeds refusent une condition mal orthographiée, qui ferait qu'une règle ne s'applique jamais.

## Résultats

Montants sur l'échantillon de 30 % : 12 209 266 courses propres, 246 750 508 $ de rémunération de base.

### Comparaison des scénarios

| Scénario | Coût du bonus | Hausse de la rémunération | Courses concernées |
|---|---|---|---|
| `BASE` | 0 $ | 0 % | 0 % |
| `SNOW_15` | 1 929 364 $ | +0,78 % | 5,27 % |
| `SNOW_165` | 2 122 300 $ | +0,86 % | 5,27 % |
| `ZONE_100` | 2 814 723 $ | +1,14 % | 23,05 % |
| `PEAK_150` | 5 757 549 $ | +2,33 % | 31,44 % |
| `COMBINED` | 10 501 636 $ | +4,26 % | [à compléter] |

- Passer le bonus neige de 15 % à 16,5 % coûte 192 936 $ de plus, soit 0,0158 $ par course
  (de 0,782 % à 0,860 % de la rémunération).
- Le coût de `COMBINED` est égal à la somme des coûts de `SNOW_15`, `PEAK_150` et `ZONE_100`
  (les règles se cumulent), ce que vérifie un test.

### Coût de chaque règle dans `COMBINED`

| Règle | Courses concernées | Coût | Par course concernée | Part du scénario |
|---|---|---|---|---|
| `R_SNOW_15` | 642 871 | 1 929 364 $ | 3,00 $ | 18,4 % |
| `R_PEAK_AM` | 972 729 | 1 459 094 $ | 1,50 $ | 13,9 % |
| `R_PEAK_PM` | 2 865 637 | 4 298 456 $ | 1,50 $ | 40,9 % |
| `R_ZONE_100` | 2 814 723 | 2 814 723 $ | 1,00 $ | 26,8 % |

Le coût d'une règle est le produit de son intensité (le montant par course concernée) et de son étendue
(le nombre de courses concernées). La neige est la règle la plus généreuse par course (3,00 $) mais ne touche que 5 %
des courses. La pointe paie 1,50 $ et en touche près d'un tiers : c'est elle qui pèse le plus (55 % du scénario combiné).

### Sensibilité du bonus neige

Le coût est une droite en fonction du taux, parce que le bonus est un pourcentage de la rémunération réelle.

| Taux | Coût | Par course | Hausse de la rémunération | Coût du palier de 5 points |
|---|---|---|---|---|
| 0 % | 0 $ | 0 $ | 0 % | |
| 5 % | 643 121 $ | 0,0527 $ | 0,261 % | 643 121 $ |
| 10 % | 1 286 243 $ | 0,1053 $ | 0,521 % | 643 121 $ |
| 15 % | 1 929 364 $ | 0,1580 $ | 0,782 % | 643 121 $ |
| 20 % | 2 572 485 $ | 0,2107 $ | 1,043 % | 643 121 $ |
| 25 % | 3 215 606 $ | 0,2634 $ | 1,303 % | 643 121 $ |
| 30 % | 3 858 728 $ | 0,3160 $ | 1,564 % | 643 121 $ |

Chaque point de taux coûte environ 128 600 $ (0,0105 $ par course).

Inversion : la rémunération de base des courses sous la neige vaut 12 862 427 $, donc le taux maximal pour un budget
donné est `budget / 12 862 427`. Sur l'échantillon, un budget de 500 000 $ permet un taux de 3,89 %, un budget de
1 000 000 $ un taux de 7,77 % et un budget de 2 000 000 $ un taux de 15,55 %.

### Heures de pointe

La première version du simulateur utilisait une hypothèse : 7h-9h59 et 16h-19h59, soit 39,8 % de la demande de
semaine pour 5 026 988 $ (+2,04 %). Elle a été vérifiée sur la demande réelle (`agg_zone_hour`) :
cinq des six heures les plus fortes étaient dans la fenêtre, mais 20h (5,52 %) et 21h (5,24 %) étaient dehors.

Heures de semaine les plus fortes (part de la demande de semaine, la demande uniforme valant 4,17 %) :
8h (6,19 %), 18h (6,18 %), 19h (5,94 %), 17h (5,86 %), 20h (5,52 %), 9h (5,35 %), 16h (5,27 %), 21h (5,24 %).

La définition retenue : les heures de semaine dont la part de la demande dépasse 1,25 fois la demande uniforme (5,2 %),
soit 8h-9h59 et 16h-21h59.

| Option | Heures | Courses (part de la semaine) | Coût | Hausse de la rémunération |
|---|---|---|---|---|
| Hypothèse de départ | 7-9 et 16-19 | 3 351 325 (39,8 %) | 5 026 988 $ | +2,04 % |
| **Retenue : part ≥ 1,25 x uniforme (5,2 %)** | **8-9 et 16-21** | **3 838 366 (45,5 %)** | **5 757 549 $** | **+2,33 %** |
| Seuil de 5,0 % | 8-9 et 15-21 | 4 264 572 (50,6 %) | 6 396 858 $ | +2,59 % |
| Seuil de 4,9 % | 7-9 et 14-22 | 5 516 962 (65,5 %) | 8 275 443 $ | +3,35 % |

Le seuil est un choix métier : à 4,9 %, la « pointe » couvrirait les deux tiers de la demande et n'en serait plus une.
La règle retenue est fragile : 21h (5,24 %) est juste au-dessus du seuil (5,21 %), 15h (5,06 %) juste en dessous.
Le profil de semaine inclut trois jours fériés (1er janvier, 19 janvier, 16 février), traités comme des jours de semaine.

## Contrôles

- Les segments retrouvent exactement les courses propres, la rémunération et le tarif de `fct_trips`.
- La situation actuelle (`BASE`) n'a aucun bonus.
- Le coût de `SNOW_165` divisé par celui de `SNOW_15` égale le rapport des taux lus dans le seed.
- Le coût de `COMBINED` égale la somme des coûts de `SNOW_15`, `PEAK_150` et `ZONE_100`.
- La grille de sensibilité, au taux de `R_SNOW_15`, retrouve le coût du scénario `SNOW_15`.
- Un taux plus élevé ne coûte jamais moins cher.
- La somme des coûts par règle égale le coût de chaque scénario.
- Les seeds refusent une condition hors des valeurs autorisées, un type de bonus inconnu ou un identifiant orphelin.
- Les heures de pointe vérifiées sur la demande réelle : les sept heures de l'hypothèse de départ additionnaient
  exactement les 3 351 325 courses attribuées par le simulateur aux règles de pointe de l'époque.

## Limites

- Montants à l'échelle de l'échantillon de 30 % : multiplier par environ 3,3 donne un ordre de grandeur pour l'ensemble
  des courses, pas un résultat. Les montants par course et les pourcentages restent valables.
- Coût statique : aucun effet sur le comportement (acceptation des courses, offre de chauffeurs).
- Règles cumulées : un scénario qui cumule plusieurs règles coûte plus cher qu'un scénario qui retiendrait
  un seul bonus par course. L'écart n'a pas été chiffré.
- Les règles de bonus sont des hypothèses. Les heures de pointe sont dérivées de la demande réelle, mais leur seuil est un choix.
- Une seule station météo : tous les quartiers ont la même météo.