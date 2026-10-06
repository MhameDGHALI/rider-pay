-- Réconciliation : le seuil de rentabilité porte sur les mêmes courses que les unités de l'expérience.
with break_even as (
    select sum(nb_trips) as n
    from {{ ref('exp_break_even') }}
),
units as (
    select sum(nb_trips) as n
    from {{ ref('exp_switchback_units') }}
)
select
    break_even.n  as break_even_trips,
    units.n       as units_trips
from break_even
cross join units
where break_even.n != units.n