# Mesure du coût de requête : fct_trips

## Contexte

- Entrepôt : BigQuery (sandbox, sans facturation).
- Données : 12 244 353 courses, échantillon de 30 % de janvier-février 2026.
- `fct_trips` : table partitionnée par plage d'entiers sur `pickup_date_key` (AAAAMMJJ),
  clusterisée par `license_num` puis `pickup_location_id`. 59 partitions remplies.
- `int_trips_enriched` : vue (non partitionnée), source de `fct_trips`.
- Méthode : volume affiché par la console avant l'exécution (estimation), en Mo
  (1 colonne de 8 octets sur 12 244 353 lignes = 93,42 Mo).

## Requête testée

Nombre de courses et total de rémunération pour le 25 janvier 2026 :

```sql
SELECT COUNT(*) AS nb_courses, ROUND(SUM(driver_pay_usd), 2) AS total_pay
FROM <source>
WHERE <filtre>;
```

Les trois premières requêtes renvoient le même nombre de courses et le même total (contrôle de justesse).

## Résultats

| # | Source | Filtre | Volume estimé |
|---|---|---|---|
| 1 | `int_trips_enriched` (vue) | `pickup_date` | 373,68 Mo |
| 2 | `fct_trips` (table) | `pickup_date_key` (clé de partition) | 1,47 Mo |
| 3 | `fct_trips` (table) | `pickup_date` (colonne non partitionnée) | 1,47 Mo |
| 4 | `fct_trips` (table) | `trip_miles > 100` (aucun élagage possible) | 183 Mo |

## Lecture

- La mesure 1 vaut 4 × 93,42 Mo : la vue lit l'équivalent de quatre colonnes complètes
  (probablement `pickup_datetime`, `driver_pay` et les deux identifiants de zone, lus à cause des jointures).
- La mesure 4 (183 Mo) est le point de comparaison sans élagage : la table lit deux colonnes en entier.
- La mesure 2 est environ 125 fois plus faible que la mesure 4 : lire un jour au lieu de toute la table.
- Le rapport de 254 entre les mesures 1 et 2 se décompose approximativement en 2 (table matérialisée
  plus étroite que la vue) et 125 (lecture d'un seul jour).
- La mesure 4 filtre sur une autre colonne que la vue : la décomposition est donc approximative.

## Observation inattendue

La mesure 3 filtre sur `pickup_date`, qui n'est pas la colonne de partitionnement. J'attendais environ
140 Mo (46,71 Mo pour `pickup_date` + 93,42 Mo pour `driver_pay`). L'estimation est de 1,47 Mo, comme pour
la mesure 2. La documentation Google que j'ai consultée indique que l'élagage de partitions suppose
un filtre sur la colonne de partitionnement. Je n'ai pas d'explication vérifiée pour cet écart.
Règle retenue : filtrer sur `pickup_date_key`, seul comportement garanti.

## Limites

- Ce sont des estimations affichées avant l'exécution, pas des octets facturés.
  À ma connaissance, BigQuery facture au minimum 10 Mo par table lue : à vérifier dans la documentation.
- Une seule requête et une seule journée ont été mesurées.
- Les partitions pèsent environ 50 Mo chacune : le partitionnement apporte un bénéfice limité à cette échelle.
- Le sandbox impose le partitionnement par entiers (voir `docs/decisions.md`).

## Conclusion

Sur cette requête, `fct_trips` lit environ 125 fois moins de données qu'une lecture complète de la table
(1,47 Mo contre 183 Mo) lorsqu'on cible un jour, et environ 254 fois moins que la vue.
La moitié du gain de la vue vers la table (environ un facteur 2) vient de la matérialisation,
le reste de l'élagage par jour. Le comportement observé avec un filtre sur `pickup_date`
reste à expliquer.