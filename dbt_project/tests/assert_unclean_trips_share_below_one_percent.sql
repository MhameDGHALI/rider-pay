-- Garde-fou : si plus de 1 % des courses sont signalées, c'est probablement un bug
-- dans la définition des indicateurs. Retourne une ligne (donc échoue) dans ce cas.
select *
from (
    select
        count(*) as nb_trips,
        countif(not is_clean_trip) as nb_not_clean,
        safe_divide(countif(not is_clean_trip), count(*)) as share_not_clean
    from {{ ref('int_trip_economics') }}
)
where share_not_clean > 0.01