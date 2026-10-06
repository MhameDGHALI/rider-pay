-- Une course "propre" doit avoir toutes ses mesures calculables et positives.
-- Retourne les courses propres dont une mesure est vide ou non positive.
select
    trip_id,
    driver_pay_usd,
    trip_seconds,
    trip_miles,
    base_passenger_fare_usd,
    driver_pay_per_trip_hour_usd,
    driver_pay_per_mile_usd,
    platform_margin_rate
from {{ ref('int_trip_economics') }}
where is_clean_trip
  and (
        driver_pay_per_trip_hour_usd is null or driver_pay_per_trip_hour_usd <= 0
     or driver_pay_per_mile_usd is null or driver_pay_per_mile_usd <= 0
     or platform_margin_rate is null
  )