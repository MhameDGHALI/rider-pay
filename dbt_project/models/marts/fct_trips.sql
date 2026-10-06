{{
    config(
        materialized='table',
        partition_by={
            "field": "pickup_date_key",
            "data_type": "int64",
            "range": {"start": 20260101, "end": 20260301, "interval": 1}
        },
        cluster_by=["license_num", "pickup_location_id"]
    )
}}

select
    -- clé de la course et clés de jointure vers les dimensions
    trip_id,
    cast(format_date('%Y%m%d', pickup_date) as int64) as pickup_date_key,
    pickup_date,
    pickup_hour_start_at,
    license_num,
    pickup_location_id,
    dropoff_location_id,

    -- horodatages (heure locale de New York)
    request_at,
    on_scene_at,
    pickup_at,
    dropoff_at,
    pickup_hour,

    -- mesures de la course
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

    -- mesures dérivées
    platform_margin_usd,
    platform_margin_rate,
    driver_pay_per_trip_hour_usd,
    driver_pay_per_mile_usd,
    driver_earnings_with_tips_usd,
    seconds_request_to_on_scene,
    seconds_on_scene_to_pickup,
    seconds_request_to_pickup,

    -- indicateurs de la course
    is_shared_request,
    is_shared_match,
    is_wav_request,
    is_wav_match,
    is_airport_trip,
    is_snowing,
    is_raining,
    is_weekend,

    -- indicateurs d'anomalies
    has_negative_driver_pay,
    has_zero_driver_pay,
    has_nonpositive_fare,
    has_nonpositive_distance,
    has_nonpositive_duration,
    has_inconsistent_duration,
    has_timeline_anomaly,
    is_clean_trip

from {{ ref('int_trips_enriched') }}