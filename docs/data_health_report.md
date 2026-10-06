# Rapport de santé des données

59 jours, 2 opérateurs, 6 indicateurs surveillés, seuil du score robuste : 4.0.

- Alertes ouvertes : **0**
- Alertes acquittées après examen : **3**
- Informations (événements attendus) : **5**

## Alertes ouvertes

Aucune.

## Alertes acquittées

| jour | opérateur | indicateur | valeur | normale | score | raison de l'acquittement |
|---|---|---|---|---|---|---|
| 2026-01-22 | HV0005 | part de courses signalées | 0.09487 | 0.0003359 | +94.5 | tarif de base nul sur 9.5 pct des courses Lyft toute la journee |
| 2026-01-23 | HV0005 | part de courses signalées | 0.1015 | 0.0003192 | +101.2 | cause non etablie |
| 2026-01-25 | HV0003 | part de courses signalées | 0.2423 | 0.0003701 | +241.9 | ; exclues des analyses par is_clean_trip |

## Informations (événements attendus)

| jour | opérateur | indicateur | valeur | normale | score | événement |
|---|---|---|---|---|---|---|
| 2026-01-25 | HV0003 | nombre de courses | 7.046e+04 | 1.513e+05 | -9.2 | heavy_snow |
| 2026-01-25 | HV0005 | nombre de courses | 2.609e+04 | 6.377e+04 | -5.8 | heavy_snow |
| 2026-02-23 | HV0003 | nombre de courses | 2.801e+04 | 1.316e+05 | -18.7 | heavy_snow |
| 2026-02-23 | HV0005 | nombre de courses | 2.008e+04 | 5.065e+04 | -6.0 | heavy_snow |
| 2026-02-24 | HV0003 | marge de la plateforme | 0.1979 | 0.251 | -4.5 | day_after_snow |
