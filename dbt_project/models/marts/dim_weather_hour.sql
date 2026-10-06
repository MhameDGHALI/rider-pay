-- Dimension météo : une ligne par heure locale de New York.
select
    observed_at,
    temperature_c,
    precipitation_mm,
    rain_mm,
    snowfall_cm,
    wind_speed_kmh,
    snowfall_cm > 0 as is_snowing,
    rain_mm > 0     as is_raining,
    case
        when snowfall_cm > 0 and rain_mm > 0 then 'mixed'
        when snowfall_cm > 0                 then 'snow'
        when rain_mm > 0                     then 'rain'
        else 'dry'
    end as weather_condition
from {{ ref('stg_weather_hourly') }}