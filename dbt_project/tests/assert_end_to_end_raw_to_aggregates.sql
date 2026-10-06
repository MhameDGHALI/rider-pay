-- Réconciliation de bout en bout : source brute -> table de faits et agrégats.
-- Compare le nombre de courses, le nombre de courses avec frais de congestion et la rémunération totale.
-- Retourne une ligne (donc échoue) si un écart apparaît.
with raw_side as (
    select
        count(*)                          as nb_trips,
        countif(cbd_congestion_fee > 0)   as nb_fee,
        sum(driver_pay)                   as total_pay
    from {{ source('raw', 'hvfhv_trips') }}
),
fct_side as (
    select sum(driver_pay_usd) as total_pay
    from {{ ref('fct_trips') }}
),
daily_side as (
    select
        sum(nb_trips)               as nb_trips,
        sum(nb_trips_with_cbd_fee)  as nb_fee
    from {{ ref('agg_daily_operator') }}
),
zone_side as (
    select
        sum(nb_trips)               as nb_trips,
        sum(nb_trips_with_cbd_fee)  as nb_fee
    from {{ ref('agg_zone_congestion') }}
)
select
    raw_side.nb_trips    as raw_trips,
    daily_side.nb_trips  as daily_trips,
    zone_side.nb_trips   as zone_trips,
    raw_side.nb_fee      as raw_fee,
    daily_side.nb_fee    as daily_fee,
    zone_side.nb_fee     as zone_fee,
    raw_side.total_pay   as raw_pay,
    fct_side.total_pay   as fct_pay
from raw_side
cross join fct_side
cross join daily_side
cross join zone_side
where raw_side.nb_trips != daily_side.nb_trips
   or raw_side.nb_trips != zone_side.nb_trips
   or raw_side.nb_fee   != daily_side.nb_fee
   or raw_side.nb_fee   != zone_side.nb_fee
   or abs(raw_side.total_pay - fct_side.total_pay) > 0.05