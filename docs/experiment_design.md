# Plan d'expérience : bonus de pointe en semaine (switchback)

## Statut

Plan rédigé avant l'injection de tout effet, puis complété (voir « Historique du plan »).
L'effet du bonus est **simulé** : aucune donnée réelle de bonus n'existe dans les données.
L'expérience valide une **méthode** (répartition, mesure, test, puissance), elle ne mesure pas un effet réel.
Les résultats des jours 13 et 14 sont inclus. Restent à compléter : coût par course supplémentaire,
règle de décision et conclusion.

## Question business

Un bonus de pointe en semaine augmente-t-il le nombre de courses réalisées pendant la pointe,
et à quel coût par course supplémentaire ?

## Hypothèses

- H0 : le bonus ne change pas le nombre de courses d'un bloc de pointe.
- H1 : le bonus augmente le nombre de courses d'un bloc de pointe.

Limite : on observe des courses réalisées, qui dépendent à la fois de l'offre (les chauffeurs) et de la demande
(les clients). Un bonus agit sur l'offre : on suppose que la demande n'est pas modifiée.

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

Contrôle de la répartition (de type SRM) : 39 unités test et 39 unités contrôle (chi-deux contre 50/50 :
p = 1,00), toutes les strates équilibrées à une unité près (les deux strates du vendredi, de 9 unités,
donnent 4 test et 5 contrôle le matin, 5 test et 4 contrôle le soir).

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

1. Contrôle de la répartition : 39 unités test et 39 unités contrôle, strates équilibrées.
2. Régression par les moindres carrés du logarithme du nombre de courses sur le traitement, la strate
   (bloc et jour de la semaine) et le nombre d'heures de neige du bloc.
3. Effet estimé, intervalle de confiance à 95 % (loi de Student) et p-value.
4. Puissance et effet minimal détectable par simulation.

## Analyse de sensibilité (exploratoire)

Le test A/A a montré un bruit plus grand que prévu, dû à quelques jours exceptionnels. Ces jours ont été
repérés **en regardant les volumes de base** : l'analyse qui les retire est donc **exploratoire** et
ne remplace pas l'analyse principale. Les deux sont présentées côte à côte.

La liste est fixée avant l'injection de tout effet, par jour entier (6 unités), dans le seed `exp_disturbed_dates` :

| Jour | Contexte | Écart des unités à leur strate |
|---|---|---|
| Lundi 23 février | Neige de 14,8 cm sur 18 heures, la veille 8,4 cm. Neige dans les deux heures du bloc du matin | Matin -87 %, soir -58 % |
| Lundi 26 janvier | Lendemain du 25 janvier (18,9 cm de neige sur 17 heures). Presque aucune neige le 26 (0,2 cm) | Matin -32 % (environ -48 % d'un lundi ordinaire) ; le soir paraît ordinaire |
| Vendredi 2 janvier | Lendemain du jour férié du 1er janvier | Matin -34 %, soir -22 % |

Précisions :
- Le soir du 26 janvier paraît ordinaire. Il est retiré quand même pour exclure des jours entiers,
  pas des unités une à une.
- Le 24 février, lendemain de la tempête du 23, ne présente pas d'écart important : « lendemain de tempête »
  n'est pas une règle générale, seulement une observation sur le 26 janvier.
- Les autres lendemains de jours fériés (20 janvier, 17 février) ne sont pas exclus : ils ne se distinguent pas.
- Bras des 6 unités perturbées : [à compléter avec la requête de contrôle : nombre dans le bras test et dans le bras contrôle].

Analyse : le même modèle de régression sur les 72 unités restantes.

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
quelques jours exceptionnels pèsent lourd en logarithme.

## Résultats de la simulation (jour 14)

Effets connus injectés dans le nombre de courses des unités du bras test : 0 % (placebo), +5 %, +15 % et +25 %.
L'effet est ajouté au logarithme du nombre de courses. Scripts : `experiments/02_effect_analysis.py` et
`experiments/03_power_curve.py`. Les résultats vérifient la méthode, ils ne disent rien de l'effet d'un bonus réel.

### Analyse sur la répartition réelle

| Effet vrai | Principale (78 unités) : estimation (IC 95 %) | p | Sensibilité (72 unités) : estimation (IC 95 %) | p |
|---|---|---|---|---|
| 0 % (placebo) | +10,0 % (-0,8 ; +21,9) | 0,069 | +1,6 % (-2,2 ; +5,6) | 0,404 |
| +5 % | +15,5 % (+4,2 ; +28,0) | 0,007 | +6,7 % (+2,7 ; +10,8) | 0,001 |
| +15 % | +26,5 % (+14,1 ; +40,1) | < 0,001 | +16,9 % (+12,5 ; +21,4) | < 0,001 |
| +25 % | +37,5 % (+24,1 ; +52,3) | < 0,001 | +27,0 % (+22,3 ; +32,0) | < 0,001 |

Erreur type : 5,14 points pour l'analyse principale, 1,91 point pour la sensibilité.
L'intervalle de confiance contient le vrai effet dans les 8 cas.

### Puissance (5 000 répartitions au hasard par analyse)

| | Principale (78 unités) | Sensibilité (72 unités) |
|---|---|---|
| Faux positifs | 4,3 % | 5,3 % |
| Erreur type moyenne | 5,23 points | 1,85 point |
| Effet minimal détectable à 80 % de puissance | 16,5 % | 5,7 % |
| Puissance à +5 % | 16 % | 73 % |
| Puissance à +15 % | 73 % | 100 % |
| Effet estimé moyen parmi les expériences qui détectent un vrai +5 % | 13,6 % | 5,9 % |
| Effet estimé moyen parmi les expériences qui détectent un vrai +15 % | 17,8 % | 15,0 % |
| Unités pour détecter +5 % à 80 % de puissance (approximation) | 702 | 81 |
| Jours de semaine correspondants | 351 (environ 70 semaines) | 41 (environ 8 semaines) |

Puissance (%) selon l'effet vrai :

| Effet vrai | 0 | 2,5 | 5 | 7,5 | 10 | 12,5 | 15 | 17,5 | 20 | 22,5 | 25 | 27,5 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Principale | 4 | 8 | 16 | 27 | 43 | 59 | 73 | 85 | 93 | 98 | 99 | 100 | 100 |
| Sensibilité | 5 | 25 | 73 | 97 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

La simulation concorde avec la théorie calculée à partir du bruit du test A/A : puissance de l'analyse principale
à +5 % de 16 % (15 % prévu), à +10 % de 43 % (43 %), à +15 % de 73 % (75 %), à +25 % de 99 % (99 %).

### Lecture

- **Un tirage unique peut tromper.** Sur la répartition réelle, le placebo de l'analyse principale donne +10,0 %
  (p = 0,069), alors que l'effet vrai est nul. Avec un vrai effet de +5 %, l'analyse principale annonce
  +15,5 % « détecté » (p = 0,007), soit le triple de la vérité. L'analyse de sensibilité donne +1,6 % au placebo
  et +6,7 % à +5 %. Hypothèse, à confirmer avec le bras des unités perturbées : les unités à volume très bas
  sont tombées surtout dans le bras contrôle.
- **Malédiction du gagnant.** À faible puissance, les expériences qui détectent un effet sont celles où le bruit a
  joué en leur faveur : parmi elles, l'effet estimé moyen vaut 13,6 % pour un vrai effet de +5 % (analyse principale).
  Un résultat significatif issu d'une expérience peu puissante surestime l'effet.
- **Six unités sur 78 (7,7 %) concentrent presque tout le bruit.** Les retirer ramène l'erreur type de 5,23 à
  1,85 point, soit une variance divisée par 8, et l'effet minimal détectable de 16,5 % à 5,7 %.
- **Ce que l'analyse principale ne peut pas voir.** Un effet de +5 % n'est détecté que dans 16 % des tirages,
  et il faudrait environ 70 semaines. Seuls des effets d'au moins 16 % sont repérés de façon fiable.
- **L'analyse principale reste inchangée.** La changer après avoir vu ces résultats reviendrait à choisir celle
  qui arrange. Le résultat est documenté et la leçon est retenue pour une prochaine expérience.

## Règle de décision

À compléter au jour 15 :
- le seuil de rentabilité : avec un bonus fixe c par course et une marge moyenne m par course,
  le bonus rapporte plus qu'il ne coûte si l'augmentation du nombre de courses dépasse c / (m - c).
  La marge m est approximative (tarif de base moins rémunération du chauffeur) ;
- la condition sur l'intervalle de confiance, qui tient compte de la faible puissance : une estimation isolée
  ne suffit pas.

## Ce qui est réel et ce qui est simulé

| Élément | Nature |
|---|---|
| Nombre de courses de chaque unité (ligne de base) | Réel |
| Météo, calendrier | Réel |
| Répartition test et contrôle | Calculée (reproductible) |
| **Effet du bonus** | **Simulé : ajouté au logarithme du nombre de courses des unités du bras test** |

Les résultats illustrent la méthode. Ils ne disent rien de l'effet d'un bonus réel.

## Risques connus

- 78 unités seulement : la puissance de l'analyse principale est faible (effet minimal détectable de 16,5 %).
- Quelques jours très creux (tempête, lendemain de tempête, lendemain de jour férié) concentrent presque tout le
  bruit : six unités expliquent environ 7/8 de la variance de l'estimation. Ils sont pesés dans l'analyse principale
  et retirés dans l'analyse de sensibilité.
- Un tirage unique peut s'écarter fortement de la vérité (placebo à +10 % dans l'analyse principale).
- Report entre blocs : le matin et le soir d'un même jour sont répartis indépendamment ; un chauffeur qui
  connaît le bonus du matin peut changer son comportement le soir.
- Une seule station météo pour toute la ville.
- Le nombre de courses réalisées mélange offre et demande.
- La puissance est calculée en considérant ces 78 unités comme fixes : elle ne vaut pas pour d'autres jours.

## Leçons pour une prochaine expérience

- Fixer à l'avance une règle d'exclusion fondée sur la météo et le calendrier (par exemple un seuil de neige
  sur la journée, les lendemains de jours fériés), plutôt que de découvrir les jours perturbés après coup.
- Prévoir une durée suffisante : environ 8 semaines hors jours perturbés pour voir +5 %.
- Présenter tout résultat avec son intervalle de confiance et sa puissance, jamais l'estimation seule.

## Reproduire

```
dbt seed --select exp_excluded_dates exp_disturbed_dates
dbt build --select exp_switchback_units exp_switchback_assignment
python experiments/01_aa_test.py
python experiments/02_effect_analysis.py
python experiments/03_power_curve.py
```

## Historique du plan

| Étape | Contenu |
|---|---|
| Jour 13, avant l'A/A | Plan rédigé : hypothèse, unité, répartition, métrique, analyse principale sur 78 unités |
| Jour 13, après l'A/A | Ajout de la méthode retenue (répartition par strate et régression) |
| Jour 13, après l'examen des unités extrêmes | Ajout de l'analyse de sensibilité exploratoire (6 unités retirées). Décision prise avant toute injection d'effet |
| Jour 14 | Injection des effets (0 %, +5 %, +15 %, +25 %), analyse sur la répartition réelle, courbe de puissance. Analyse principale inchangée |
| Jour 15 | À compléter : coût par course supplémentaire, règle de décision, conclusion |