-- Agrégat par zone de départ, heure de la journée et type de jour (semaine ou week-end).
-- Pour des cartes de chaleur. Filtrer sur nb_clean_trips : les petites cellules sont bruitées.
select
    concat(
        cast(pickup_location_id as string), '-',
        cast(pickup_hour as string), '-',
        if(is_weekend, 'we', 'wd')
    )                                                           as agg_key,
    pickup_location_id,
    pickup_hour,
    is_weekend,

    count(*)                                                    as nb_trips,
    countif(is_clean_trip)                                      as nb_clean_trips,
    countif(cbd_congestion_fee_usd > 0)                         as nb_trips_with_cbd_fee,

    sum(if(is_clean_trip, driver_pay_usd, 0))                   as clean_driver_pay_usd,
    sum(if(is_clean_trip, base_passenger_fare_usd, 0))          as clean_base_fare_usd,
    sum(if(is_clean_trip, trip_seconds, 0))                     as clean_trip_seconds,

    safe_divide(
        sum(if(is_clean_trip, driver_pay_usd, 0)),
        countif(is_clean_trip)
    )                                                           as avg_clean_driver_pay_usd,
    safe_divide(
        sum(if(is_clean_trip, driver_pay_usd, 0)),
        sum(if(is_clean_trip, trip_seconds, 0)) / 3600
    )                                                           as clean_driver_pay_per_trip_hour_usd,
    approx_quantiles(
        if(not has_timeline_anomaly, seconds_request_to_pickup, null), 100
    )[offset(50)]                                               as median_wait_request_to_pickup_s

from {{ ref('fct_trips') }}
group by pickup_location_id, pickup_hour, is_weekend