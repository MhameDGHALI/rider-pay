-- Dimension des zones TLC. Utilisée pour la zone de départ ET la zone d'arrivée.
select
    location_id,
    borough,
    zone_name,
    concat(zone_name, ' (', cast(location_id as string), ')') as zone_label,
    service_zone,
    borough = 'Manhattan'                  as is_manhattan,
    service_zone in ('Airports', 'EWR')    as is_airport_zone
from {{ ref('stg_taxi_zones') }}