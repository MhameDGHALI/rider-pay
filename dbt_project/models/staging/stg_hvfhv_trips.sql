-- Staging des courses HVFHS (Uber, Lyft).
-- Renommage, typage, conversion TIMESTAMP -> DATETIME. Aucune règle métier, aucune ligne supprimée.
--
-- Les heures TLC sont en heure LOCALE de New York, sans fuseau. BigQuery les a chargées
-- comme des TIMESTAMP (UTC) : les chiffres sont justes, seule l'étiquette est fausse.
-- datetime(<timestamp>) SANS fuseau en second argument garde exactement les mêmes chiffres.
-- Ne jamais écrire datetime(x, 'America/New_York') : cela décalerait toutes les heures.

select
    trip_id,
    hvfhs_license_num                      as license_num,
    originating_base_num,

    datetime(request_datetime)             as request_at,
    datetime(on_scene_datetime)            as on_scene_at,
    datetime(pickup_datetime)              as pickup_at,
    datetime(dropoff_datetime)             as dropoff_at,

    cast(PULocationID as int64)            as pickup_location_id,
    cast(DOLocationID as int64)            as dropoff_location_id,

    cast(trip_miles as float64)            as trip_miles,
    cast(trip_time as int64)               as trip_seconds,

    cast(base_passenger_fare as float64)   as base_passenger_fare_usd,
    cast(tolls as float64)                 as tolls_usd,
    cast(bcf as float64)                   as black_car_fund_usd,
    cast(sales_tax as float64)             as sales_tax_usd,
    cast(congestion_surcharge as float64)  as congestion_surcharge_usd,
    cast(airport_fee as float64)           as airport_fee_usd,
    cast(cbd_congestion_fee as float64)    as cbd_congestion_fee_usd,
    cast(tips as float64)                  as tips_usd,
    cast(driver_pay as float64)            as driver_pay_usd,

    {{ yn_to_bool('shared_request_flag') }} as is_shared_request,
    {{ yn_to_bool('shared_match_flag') }}   as is_shared_match,
    {{ yn_to_bool('wav_request_flag') }}    as is_wav_request,
    {{ yn_to_bool('wav_match_flag') }}      as is_wav_match

from {{ source('raw', 'hvfhv_trips') }}