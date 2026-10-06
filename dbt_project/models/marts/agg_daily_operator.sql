-- Agrégat journalier par opérateur. Les colonnes clean_* portent sur les courses propres.
-- Les sommes et compteurs sont additifs ; les ratios ne le sont pas (les recalculer en BI).
select
    concat(cast(pickup_date_key as string), '-', license_num)   as agg_key,
    pickup_date_key,
    license_num,

    count(*)                                                    as nb_trips,
    countif(is_clean_trip)                                      as nb_clean_trips,
    countif(cbd_congestion_fee_usd > 0)                         as nb_trips_with_cbd_fee,

    sum(if(is_clean_trip, driver_pay_usd, 0))                   as clean_driver_pay_usd,
    sum(if(is_clean_trip, base_passenger_fare_usd, 0))          as clean_base_fare_usd,
    sum(if(is_clean_trip, tips_usd, 0))                         as clean_tips_usd,
    sum(if(is_clean_trip, trip_seconds, 0))                     as clean_trip_seconds,
    sum(if(is_clean_trip, trip_miles, 0))                       as clean_trip_miles,

    safe_divide(
        sum(if(is_clean_trip, driver_pay_usd, 0)),
        countif(is_clean_trip)
    )                                                           as avg_clean_driver_pay_usd,
    safe_divide(
        sum(if(is_clean_trip, driver_pay_usd, 0)),
        sum(if(is_clean_trip, trip_seconds, 0)) / 3600
    )                                                           as clean_driver_pay_per_trip_hour_usd,
    1 - safe_divide(
        sum(if(is_clean_trip, driver_pay_usd, 0)),
        sum(if(is_clean_trip, base_passenger_fare_usd, 0))
    )                                                           as clean_platform_margin_rate,
    approx_quantiles(
        if(not has_timeline_anomaly, seconds_request_to_pickup, null), 100
    )[offset(50)]                                               as median_wait_request_to_pickup_s

from {{ ref('fct_trips') }}
group by pickup_date_key, license_num