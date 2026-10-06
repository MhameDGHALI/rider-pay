# Test A/A du switchback

2000 répartitions au hasard sur 78 unités réelles, sans aucun effet injecté.
Un test correct se trompe environ 5 % du temps et n'a pas de biais.

| méthode | faux positifs (%) | biais moyen (%) | écart-type de l'effet (%) | effet minimal détectable approx. (%) |
|---|---|---|---|---|
| Répartition complète, différence simple | 4.5 | 0.03 | 14.05 | 39.3 |
| Répartition complète, régression (strate + neige) | 4.5 | -0.06 | 5.52 | 15.5 |
| Répartition par strate, différence simple | 0.0 | 0.24 | 7.09 | 19.8 |
| Répartition par strate, régression (strate + neige) | 4.6 | 0.17 | 5.25 | 14.7 |
