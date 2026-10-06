-- Staging zones TLC : snake_case et remplacement des 'N/A' par 'Unknown'.
select
    cast(LocationID as int64)                         as location_id,
    coalesce(nullif(Borough, 'N/A'), 'Unknown')       as borough,
    coalesce(nullif(Zone, 'N/A'), 'Unknown')          as zone_name,
    coalesce(nullif(service_zone, 'N/A'), 'Unknown')  as service_zone
from {{ ref('taxi_zone_lookup') }}