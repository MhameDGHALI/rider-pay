-- Réconciliation : les segments doivent retrouver exactement les courses propres de fct_trips.
with seg as (
    select
        sum(nb_trips)        as nb_trips,
        sum(driver_pay_usd)  as pay,
        sum(base_fare_usd)   as fare
    from {{ ref('sim_trip_segments') }}
),
fct as (
    select
        count(*)                       as nb_trips,
        sum(driver_pay_usd)            as pay,
        sum(base_passenger_fare_usd)   as fare
    from {{ ref('fct_trips') }}
    where is_clean_trip
)
select
    seg.nb_trips as seg_trips, fct.nb_trips as fct_trips,
    seg.pay as seg_pay,        fct.pay as fct_pay,
    seg.fare as seg_fare,      fct.fare as fct_fare
from seg
cross join fct
where seg.nb_trips != fct.nb_trips
   or abs(seg.pay  - fct.pay)  > 0.05
   or abs(seg.fare - fct.fare) > 0.05