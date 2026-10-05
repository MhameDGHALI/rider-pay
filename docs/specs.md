# Spécification : Marketplace Rider Pay & Experimentation Platform

## Objectif
Mesurer et simuler l'effet de changements de rémunération (bonus) sur le coût par
course d'une marketplace de livraison, et valider ces changements par expérimentation.

## Périmètre
- Ville : New York
- Période : janvier et février 2026
- Échantillon aléatoire de 30 % des courses (seed 42), soit environ 12,6 M de courses attendues
- Entrepôt : BigQuery (sandbox, sans facturation)

## Sources de données
| Source | Nature | Contenu |
|---|---|---|
| NYC TLC HVFHS (Uber, Lyft) | Réelle | Courses, tarif, rémunération chauffeur, pourboires, péage |
| NYC TLC taxi_zone_lookup | Réelle | Zones, quartiers |
| Open-Meteo (archive) | Réelle | Température, pluie, neige, vent, par heure |
| Table des riders | Synthétique | 5 000 riders générés (seed 42) |
| Règles de bonus | Synthétique | Hypothèses de scénario (seeds dbt) |
| Affectation A/B et effet | Synthétique | Sert à illustrer la méthode, pas un effet réel |

## Indicateurs
| KPI | Question business | Calcul |
|---|---|---|
| Rémunération par heure | Les riders sont-ils bien payés ? | driver_pay / durée de la course |
| Part plateforme | Quelle marge garde la plateforme ? | 1 - driver_pay / base_passenger_fare |
| Temps d'attente | Où l'efficacité est-elle faible ? | request_datetime → pickup_datetime |
| Effet météo | La neige change-t-elle la rémunération et la demande ? | Courses jointes à la météo horaire |
| Effet du péage | Que change cbd_congestion_fee ? | Comparaison avec et sans frais |
| Coût d'un scénario | Combien coûte un bonus de plus ? | Simulateur (seeds dbt) |

## Décisions ouvertes
- [ ] Règles de bonus à simuler (neige, heure de pointe, zone)
- [ ] Niveau de l'A/B : par rider ou par zone et créneau
- [ ] Plafond de coût par requête pour l'assistant IA