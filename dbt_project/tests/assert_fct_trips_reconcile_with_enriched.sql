-- Réconciliation : fct_trips doit contenir exactement les mêmes courses et les mêmes totaux
-- que int_trips_enriched. Retourne une ligne (donc échoue) si un écart apparaît.
with src as (
    select
        count(*)                          as n,
        sum(driver_pay_usd)               as pay,
        sum(base_passenger_fare_usd)      as fare,
        sum(tips_usd)                     as tips
    from {{ ref('int_trips_enriched') }}
),
fct as (
    select
        count(*)                          as n,
        sum(driver_pay_usd)               as pay,
        sum(base_passenger_fare_usd)      as fare,
        sum(tips_usd)                     as tips
    from {{ ref('fct_trips') }}
)
select
    src.n as src_rows,   fct.n as fct_rows,
    src.pay as src_pay,  fct.pay as fct_pay,
    src.fare as src_fare, fct.fare as fct_fare,
    src.tips as src_tips, fct.tips as fct_tips
from src
cross join fct
where src.n != fct.n
   or abs(src.pay  - fct.pay)  > 0.01
   or abs(src.fare - fct.fare) > 0.01
   or abs(src.tips - fct.tips) > 0.01