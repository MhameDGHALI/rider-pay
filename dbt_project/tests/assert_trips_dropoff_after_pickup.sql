-- Courses dont la dépose est antérieure à la prise en charge. Échoue si au moins une ligne.
select trip_id, pickup_at, dropoff_at
from {{ ref('stg_hvfhv_trips') }}
where dropoff_at < pickup_at