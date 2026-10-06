-- Intermediate : courses enrichies du contexte géographique et météo.
-- LEFT JOIN uniquement : aucune course n'est supprimée.
-- Les clés de jointure (location_id, observed_at) sont uniques, donc aucun doublon n'est créé.

with trips as (

    select * from {{ ref('int_trip_economics') }}

),

zones as (

    select
        location_id,
        borough,
        zone_name,
        service_zone
    from {{ ref('stg_taxi_zones') }}

),

weather as (

    select
        observed_at,
        temperature_c,
        precipitation_mm,
        rain_mm,
        snowfall_cm,
        wind_speed_kmh
    from {{ ref('stg_weather_hourly') }}

)

select
    trips.*,

    -- zones de départ et d'arrivée
    pickup_zones.borough            as pickup_borough,
    pickup_zones.zone_name          as pickup_zone_name,
    pickup_zones.service_zone       as pickup_service_zone,
    dropoff_zones.borough           as dropoff_borough,
    dropoff_zones.zone_name         as dropoff_zone_name,
    dropoff_zones.service_zone      as dropoff_service_zone,

    -- météo de l'heure de prise en charge (station unique pour toute la ville)
    weather.temperature_c,
    weather.precipitation_mm,
    weather.rain_mm,
    weather.snowfall_cm,
    weather.wind_speed_kmh,
    weather.snowfall_cm > 0         as is_snowing,
    weather.rain_mm > 0             as is_raining,
    weather.observed_at is not null as has_weather,

    -- course touchant un aéroport (départ ou arrivée)
    (   pickup_zones.service_zone  in ('Airports', 'EWR')
     or dropoff_zones.service_zone in ('Airports', 'EWR')
    )                               as is_airport_trip

from trips
left join zones as pickup_zones
    on trips.pickup_location_id = pickup_zones.location_id
left join zones as dropoff_zones
    on trips.dropoff_location_id = dropoff_zones.location_id
left join weather
    on trips.pickup_hour_start_at = weather.observed_at