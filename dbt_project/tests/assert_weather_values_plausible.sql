-- Retourne les lignes météo aberrantes. Le test échoue si au moins une ligne est retournée.
select *
from {{ ref('stg_weather_hourly') }}
where snowfall_cm < 0
   or rain_mm < 0
   or precipitation_mm < 0
   or wind_speed_kmh < 0
   or temperature_c not between -50 and 50