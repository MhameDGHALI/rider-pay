-- Réconciliation : l'agrégat du frais de congestion doit retrouver les totaux de fct_trips.
with agg as (
    select
        sum(nb_trips)               as nb_trips,
        sum(nb_trips_with_cbd_fee)  as nb_fee
    from {{ ref('agg_zone_congestion') }}
),
fct as (
    select
        count(*)                              as nb_trips,
        countif(cbd_congestion_fee_usd > 0)   as nb_fee
    from {{ ref('fct_trips') }}
)
select
    agg.nb_trips as agg_trips, fct.nb_trips as fct_trips,
    agg.nb_fee as agg_fee,     fct.nb_fee as fct_fee
from agg
cross join fct
where agg.nb_trips != fct.nb_trips
   or agg.nb_fee != fct.nb_fee