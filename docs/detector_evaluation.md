# Sensibilité du détecteur

60 anomalies injectées par indicateur et par taille, sur des jours ordinaires des vraies données ; seuil 4.0.
Une anomalie est « détectée » si une alerte est levée sur le bon jour, le bon opérateur et le bon indicateur.

| indicateur | taille 1 | taille 2 | taille 3 | taille 4 |
|---|---|---|---|---|
| nombre de courses | -10 % : 0 % | -20 % : 5 % | -30 % : 27 % | -50 % : 75 % |
| rémunération moyenne par course | +2 % : 0 % | +5 % : 0 % | +10 % : 2 % | +25 % : 28 % |
| marge de la plateforme | -1 pt : 0 % | -2 pts : 0 % | -4 pts : 13 % | -8 pts : 85 % |
| part de courses signalées | +0,2 pt : 0 % | +0,5 pt : 100 % | +1 pt : 100 % | +5 pts : 100 % |
| part de chronologies incohérentes | +0,5 pt : 0 % | +1 pt : 5 % | +2 pts : 67 % | +5 pts : 100 % |
| part de courses avec frais de congestion | -2 pts : 0 % | -5 pts : 0 % | -10 pts : 35 % | -20 pts : 98 % |

Les anomalies sont injectées dans le sens qui dégrade la donnée, une à la fois, sur un seul jour.
Une dérive lente qui toucherait tous les jours n'est pas testée.
