-- Courses dont la prise en charge est hors de janvier-février 2026. Échoue si au moins une ligne.
select trip_id, pickup_at
from {{ ref('stg_hvfhv_trips') }}
where pickup_at < datetime '2026-01-01 00:00:00'
   or pickup_at >= datetime '2026-03-01 00:00:00'