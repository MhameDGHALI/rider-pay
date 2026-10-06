-- Le calendrier doit être continu : une ligne par jour, sans trou ni doublon.
-- Retourne une ligne (donc échoue) si le nombre de jours ne correspond pas à l'intervalle.
select *
from (
    select
        count(*)                                           as nb_days,
        count(distinct date_key)                           as nb_keys,
        date_diff(max(date_day), min(date_day), day) + 1   as expected_days
    from {{ ref('dim_date') }}
)
where nb_days != expected_days
   or nb_keys != nb_days