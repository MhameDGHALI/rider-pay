-- Réconciliation : l'agrégat journalier doit retrouver exactement les totaux de fct_trips.
with agg as (
    select
        sum(nb_trips)               as nb_trips,
        sum(nb_clean_trips)         as nb_clean_trips,
        sum(nb_trips_with_cbd_fee)  as nb_fee,
        sum(clean_driver_pay_usd)   as clean_pay
    from {{ ref('agg_daily_operator') }}
),
fct as (
    select
        count(*)                                   as nb_trips,
        countif(is_clean_trip)                     as nb_clean_trips,
        countif(cbd_congestion_fee_usd > 0)        as nb_fee,
        sum(if(is_clean_trip, driver_pay_usd, 0))  as clean_pay
    from {{ ref('fct_trips') }}
)
select
    agg.nb_trips as agg_trips,   fct.nb_trips as fct_trips,
    agg.nb_clean_trips as agg_clean, fct.nb_clean_trips as fct_clean,
    agg.nb_fee as agg_fee,       fct.nb_fee as fct_fee,
    agg.clean_pay as agg_pay,    fct.clean_pay as fct_pay
from agg
cross join fct
where agg.nb_trips != fct.nb_trips
   or agg.nb_clean_trips != fct.nb_clean_trips
   or agg.nb_fee != fct.nb_fee
   or abs(agg.clean_pay - fct.clean_pay) > 0.05