# Plan d'expérience : bonus de pointe en semaine (switchback)

## Statut

Plan rédigé avant l'injection de tout effet, puis complété après le test A/A (voir « Historique du plan »).
L'effet du bonus est **simulé** : aucune donnée réelle de bonus n'existe dans les données.
L'expérience valide une **méthode** (répartition, mesure, test, puissance), elle ne mesure pas un effet réel.

## Question business

Un bonus de pointe en semaine augmente-t-il le nombre de courses réalisées pendant la pointe,
et à quel coût par course supplémentaire ?

## Hypothèses

- H0 : le bonus ne change pas le nombre de courses d'un bloc de pointe.
- H1 : le bonus augmente le nombre de courses d'un bloc de pointe.

Limite de l'hypothèse : on observe des courses réalisées, qui dépendent à la fois de l'offre (les chauffeurs)
et de la demande (les clients). Un bonus agit sur l'offre : on suppose que la demande n'est pas modifiée.

## Traitement

Bonus fixe de 1,50 $ par course réalisée pendant le bloc (règle `PEAK_150` du simulateur).

## Unité et blocs

Une unité est un jour de semaine multiplié par un bloc de pointe :
- matin : 8h00 à 9h59 ;
- soir : 16h00 à 21h59.

Les heures sont lues dans le seed `sim_rules` (règles `R_PEAK_AM` et `R_PEAK_PM`) : le simulateur et
l'expérience partagent la même définition. Toute la ville est traitée ou non en même temps (switchback).

Trois jours fériés sont exclus dès la construction des unités (1er janvier, 19 janvier, 16 février) :
la demande y est différente. Estimation indirecte : le matin d'un jour férié compte environ 60 % des courses
d'un jour ordinaire, le soir environ 83 %.

Résultat : **78 unités**, 39 matins et 39 soirs.

| Bloc | Unités | Courses moyennes | Écart-type | Variation |
|---|---|---|---|---|
| Matin | 39 | 23 846 | 4 575 | 19,2 % |
| Soir | 39 | 69 054 | 12 146 | 17,6 % |

## Répartition

Aléatoire, **stratifiée** par bloc et par jour de la semaine : 10 strates (5 jours x 2 blocs) de 6 à 9 unités.
Dans chaque strate, les unités sont classées par une empreinte de leur identifiant et d'une graine
(`switchback_v1`), puis alternent entre test et contrôle. La strate de taille impaire donne son unité
supplémentaire au test ou au contrôle selon un tirage propre à la strate.

Implémentation : modèle dbt `exp_switchback_assignment`. La répartition ne dépend d'aucun résultat.
**La graine est figée : on ne la change pas après avoir vu un résultat.**

Résultat : 39 unités test et 39 unités contrôle, toutes les strates équilibrées à une unité près
(les deux strates du vendredi, de 9 unités, donnent 4 test et 5 contrôle le matin, 5 test et 4 contrôle le soir).

Écart de hasard observé avant tout traitement : le matin du groupe test compte 24 517 courses contre
23 209 pour le contrôle (+5,6 %), le soir 69 208 contre 68 892 (+0,46 %). Un écart de cette taille
peut apparaître sans aucun effet : une comparaison à l'oeil serait trompeuse.

## Pourquoi un switchback et pas un A/B par chauffeur

Les chauffeurs d'une même zone se partagent les mêmes commandes. Un bonus donné à la moitié d'entre eux
leur ferait prendre des commandes qui seraient allées aux autres : l'écart mesuré surestimerait l'effet
d'un bonus donné à tous (interférence). En alternant dans le temps sur toute la ville, personne ne partage
une commande avec quelqu'un d'un autre bras.

Le switchback a un coût : peu d'unités, donc peu de puissance (voir plus bas).

## Métrique principale

Nombre de courses propres de l'unité, en logarithme : l'effet se lit en pourcentage.

## Garde-fous

- Coût du bonus (par le simulateur) et coût par course supplémentaire (à calculer au jour 15).
- Covariable : nombre d'heures de neige dans le bloc.

## Analyse principale (fixée à l'avance)

Les 78 unités.

1. Contrôle de la répartition : 39 unités test et 39 unités contrôle, strates équilibrées (de type SRM).
2. Régression par les moindres carrés du logarithme du nombre de courses sur le traitement, la strate
   (bloc et jour de la semaine) et le nombre d'heures de neige du bloc.
3. Effet estimé, intervalle de confiance à 95 % (loi de Student) et p-value.
4. Puissance et effet minimal détectable par simulation.

## Analyse de sensibilité (exploratoire)

Le test A/A a montré un bruit plus grand que prévu, dû à quelques jours exceptionnels. Ces jours ont été
repérés **en regardant les volumes de base** : l'analyse qui les retire est donc **exploratoire** et
ne remplace pas l'analyse principale. Les deux sont présentées côte à côte.

La liste est fixée avant l'injection de tout effet, par jour entier (6 unités) pour ne pas choisir les unités une à une :

| Jour | Contexte | Écart des unités à leur strate |
|---|---|---|
| Lundi 23 février | Neige de 14,8 cm sur 18 heures, la veille 8,4 cm. Neige dans les deux heures du bloc du matin | Matin -87 %, soir -58 % |
| Lundi 26 janvier | Lendemain du 25 janvier (18,9 cm de neige sur 17 heures). Presque aucune neige le 26 (0,2 cm) | Matin -32 % (environ -48 % d'un lundi ordinaire) ; le soir paraît ordinaire |
| Vendredi 2 janvier | Lendemain du jour férié du 1er janvier | Matin -34 %, soir -22 % |

Précisions :
- Le soir du 26 janvier paraît ordinaire (hors des douze plus gros écarts). Il est retiré quand même pour
  exclure des jours entiers, pas des unités une à une.
- Le 24 février, lendemain de la tempête du 23, ne présente pas d'écart important : « lendemain de tempête »
  n'est donc pas une règle générale, seulement une observation sur le 26 janvier.
- Les jours fériés suivants (20 janvier, 17 février) ne sont pas exclus : ils ne se distinguent pas.

Analyse : le même modèle de régression sur les 72 unités restantes.

## Puissance et effet minimal détectable

Test A/A (voir ci-dessous) : l'écart-type de l'effet estimé est de 5,25 points de logarithme avec la
méthode retenue, soit un effet minimal détectable d'environ 14,7 points (15,8 % en niveau) à 80 % de puissance.

Prévision théorique, par approximation (à vérifier par simulation au jour 14) :

| Effet vrai | Puissance approximative |
|---|---|
| +4 % | 12 % |
| +8 % | 32 % |
| +10 % | 47 % |
| +15 % | 80 % |
| +20 % | 96 % |

Pour détecter +4 % avec 80 % de puissance, il faudrait environ 1 100 unités, soit plus de deux ans
de jours de semaine, avec le niveau de bruit actuel.

Effets simulés au jour 14 (valeurs proposées, à confirmer) : 0 %, +5 %, +15 % et +25 % (cas détaillés),
et une courbe de puissance de 0 à 30 %, tracée pour les deux analyses.

## Résultat du test A/A

2 000 répartitions au hasard sur les 78 unités réelles, sans aucun effet injecté
(`experiments/01_aa_test.py`, résultats dans `docs/aa_test_results.md`).

| Méthode | Faux positifs | Biais moyen | Écart-type de l'effet | Effet minimal détectable |
|---|---|---|---|---|
| Répartition complète, différence simple | 4,5 % | 0,03 | 14,05 | 39,3 |
| Répartition complète, régression (strate + neige) | 4,5 % | -0,06 | 5,52 | 15,5 |
| Répartition par strate, différence simple | **0,0 %** | 0,24 | 7,09 | 19,8 |
| **Répartition par strate, régression (strate + neige)** | **4,6 %** | 0,17 | **5,25** | **14,7** |

(écarts-types et effets minimaux en points de pourcentage de logarithme)

- Trois méthodes sur quatre se trompent environ 5 % du temps : elles sont bien calibrées.
- Les biais sont du hasard d'échantillonnage (moins de 1,5 erreur type).
- Une répartition par strate analysée par une différence simple donne 0 % de faux positifs : le test ignore
  que la répartition est équilibrée, surestime le bruit et ne rejette jamais, même sans effet. Il est trop prudent.
- La régression divise la variance par environ 7 par rapport à la différence simple sur une répartition complète :
  c'est comme avoir 7 fois plus d'unités.
- La méthode retenue est la répartition par strate avec régression.

Le bruit résiduel est d'environ 23 % par unité, plus que la variation de 17 à 19 % des volumes bruts :
quelques jours exceptionnels (voir l'analyse de sensibilité) pèsent lourd en logarithme.
Si le bruit tombait vers 10 %, l'effet minimal détectable passerait d'environ 15 à 6-7 points : hypothèse
de calcul, à mesurer.

## Règle de décision

À compléter au jour 15 :
- le seuil de rentabilité : avec un bonus fixe c par course et une marge moyenne m par course,
  le bonus rapporte plus qu'il ne coûte si l'augmentation du nombre de courses dépasse c / (m - c).
  La marge m est approximative (tarif de base moins rémunération du chauffeur) ;
- la condition sur l'intervalle de confiance.

## Ce qui est réel et ce qui est simulé

| Élément | Nature |
|---|---|
| Nombre de courses de chaque unité (ligne de base) | Réel |
| Météo, calendrier | Réel |
| Répartition test et contrôle | Calculée (reproductible) |
| **Effet du bonus** | **Simulé : ajouté au logarithme du nombre de courses des unités du bras test** |

Les résultats illustrent la méthode. Ils ne disent rien de l'effet d'un bonus réel.

## Risques connus

- 78 unités seulement : la puissance est faible et l'effet minimal détectable élevé (environ 15 %).
- Quelques jours très creux (tempête, lendemain de tempête, lendemain de jour férié) augmentent le bruit :
  ils sont pesés dans l'analyse principale et retirés dans l'analyse de sensibilité.
- Report entre blocs : le matin et le soir d'un même jour sont répartis indépendamment ; un chauffeur qui
  connaît le bonus du matin peut changer son comportement le soir.
- Une seule station météo pour toute la ville.
- Le nombre de courses réalisées mélange offre et demande.

## Reproduire

```
dbt seed --select exp_excluded_dates
dbt build --select exp_switchback_units exp_switchback_assignment
python experiments/01_aa_test.py
```

## Historique du plan

| Étape | Contenu |
|---|---|
| Jour 13, avant l'A/A | Plan rédigé : hypothèse, unité, répartition, métrique, analyse principale sur 78 unités |
| Jour 13, après l'A/A | Ajout de la méthode retenue (répartition par strate et régression) |
| Jour 13, après l'examen des unités extrêmes | Ajout de l'analyse de sensibilité exploratoire (6 unités retirées). Décision prise avant toute injection d'effet |
| Jour 14 | À compléter : effets simulés, résultats, courbe de puissance |
| Jour 15 | À compléter : coût par course supplémentaire, règle de décision, conclusion |