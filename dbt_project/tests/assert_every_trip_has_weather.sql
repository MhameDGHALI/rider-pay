-- Chaque course doit trouver sa ligne de météo (la météo couvre toute la période).
-- Retourne les courses sans météo ; le test échoue s'il y en a.
select trip_id, pickup_at, pickup_hour_start_at
from {{ ref('int_trips_enriched') }}
where not has_weather