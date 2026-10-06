-- Staging météo : renommage et typage uniquement.
-- Une ligne par heure locale de New York.
select
    cast(`time` as datetime)        as observed_at,
    cast(temperature_2m as float64) as temperature_c,
    cast(precipitation as float64)  as precipitation_mm,
    cast(rain as float64)           as rain_mm,
    cast(snowfall as float64)       as snowfall_cm,
    cast(wind_speed_10m as float64) as wind_speed_kmh
from {{ source('raw', 'weather_hourly') }}