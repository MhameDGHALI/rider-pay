-- Une ligne par heure, sans trou : le nombre de lignes doit être égal au nombre d'heures
-- entre la première et la dernière observation. Retourne une ligne si ce n'est pas le cas.
select *
from (
    select
        count(*) as nb_rows,
        datetime_diff(max(observed_at), min(observed_at), hour) + 1 as expected_rows
    from {{ ref('stg_weather_hourly') }}
)
where nb_rows != expected_rows