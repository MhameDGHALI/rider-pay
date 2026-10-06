-- Intermediate : économie de chaque course.
-- Ajoute des variables de calendrier, des mesures économiques, des durées d'attente
-- et des indicateurs d'anomalies. Aucune ligne n'est supprimée.

with trips as (

    select
        trip_id,
        license_num,
        request_at,
        on_scene_at,
        pickup_at,
        dropoff_at,
        pickup_location_id,
        dropoff_location_id,
        trip_miles,
        trip_seconds,
        base_passenger_fare_usd,
        tolls_usd,
        black_car_fund_usd,
        sales_tax_usd,
        congestion_surcharge_usd,
        airport_fee_usd,
        cbd_congestion_fee_usd,
        tips_usd,
        driver_pay_usd,
        is_shared_request,
        is_shared_match,
        is_wav_request,
        is_wav_match
    from {{ ref('stg_hvfhv_trips') }}

),

features as (

    select
        trips.*,

        -- calendrier (heures locales de New York)
        date(pickup_at)                                  as pickup_date,
        datetime_trunc(pickup_at, hour)                  as pickup_hour_start_at,
        extract(hour from pickup_at)                     as pickup_hour,
        extract(dayofweek from pickup_at)                as pickup_day_of_week,   -- 1 = dimanche, 7 = samedi
        extract(dayofweek from pickup_at) in (1, 7)      as is_weekend,

        -- économie de la course
        base_passenger_fare_usd - driver_pay_usd         as platform_margin_usd,
        case
            when base_passenger_fare_usd > 0
                then safe_divide(base_passenger_fare_usd - driver_pay_usd, base_passenger_fare_usd)
        end                                              as platform_margin_rate,
        safe_divide(driver_pay_usd, trip_seconds / 3600.0) as driver_pay_per_trip_hour_usd,
        safe_divide(driver_pay_usd, trip_miles)          as driver_pay_per_mile_usd,
        driver_pay_usd + tips_usd                        as driver_earnings_with_tips_usd,

        -- chronologie de la course, en secondes
        datetime_diff(on_scene_at, request_at, second)   as seconds_request_to_on_scene,
        datetime_diff(pickup_at, on_scene_at, second)    as seconds_on_scene_to_pickup,
        datetime_diff(pickup_at, request_at, second)     as seconds_request_to_pickup

    from trips

),

flagged as (

    select
        features.*,

        -- indicateurs d'anomalies (on signale, on ne supprime pas)
        driver_pay_usd < 0                               as has_negative_driver_pay,
        driver_pay_usd = 0                               as has_zero_driver_pay,
        base_passenger_fare_usd <= 0                     as has_nonpositive_fare,
        trip_miles <= 0                                  as has_nonpositive_distance,
        trip_seconds <= 0                                as has_nonpositive_duration,
        abs(trip_seconds - datetime_diff(dropoff_at, pickup_at, second)) > 1
                                                         as has_inconsistent_duration,
        (request_at > on_scene_at or on_scene_at > pickup_at)
                                                         as has_timeline_anomaly

    from features

)

select
    flagged.*,
    not (
        has_negative_driver_pay
        or has_zero_driver_pay
        or has_nonpositive_fare
        or has_nonpositive_distance
        or has_nonpositive_duration
        or has_inconsistent_duration
    ) as is_clean_trip
from flagged