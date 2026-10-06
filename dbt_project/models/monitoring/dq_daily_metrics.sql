-- Indicateurs quotidiens de santé des données, par jour et par opérateur.
-- Ils alimentent la surveillance (monitoring/run_checks.py).
-- Les événements attendus (jours fériés, forte neige, lendemains) sont déduits du calendrier et de la météo,
-- jamais des volumes : une règle fixée à l'avance et reproductible.

with trips as (

    select
        pickup_date,
        license_num,
        count(*)                                            as nb_trips,
        countif(is_clean_trip)                              as nb_clean_trips,
        countif(not is_clean_trip)                          as nb_flagged_trips,
        countif(has_timeline_anomaly)                       as nb_timeline_anomalies,
        countif(cbd_congestion_fee_usd > 0)                 as nb_trips_with_cbd_fee,
        sum(if(is_clean_trip, driver_pay_usd, 0))           as clean_driver_pay_usd,
        sum(if(is_clean_trip, base_passenger_fare_usd, 0))  as clean_base_fare_usd
    from {{ ref('fct_trips') }}
    group by pickup_date, license_num

),

snow_by_day as (

    select
        date(observed_at)     as snow_date,
        sum(snowfall_cm)      as snowfall_cm
    from {{ ref('dim_weather_hour') }}
    group by 1

),

calendar as (

    select
        d.date_day,
        d.day_of_week,
        coalesce(s.snowfall_cm, 0)                                   as snowfall_cm,
        coalesce(s.snowfall_cm, 0) >= {{ var('dq_snow_day_cm') }}    as is_heavy_snow_day,
        h.excluded_date is not null                                  as is_holiday
    from {{ ref('dim_date') }} as d
    left join snow_by_day as s
        on d.date_day = s.snow_date
    left join {{ ref('exp_excluded_dates') }} as h
        on d.date_day = h.excluded_date

),

with_previous as (

    select
        calendar.*,
        coalesce(lag(is_heavy_snow_day) over (order by date_day), false)  as is_day_after_snow,
        coalesce(lag(is_holiday) over (order by date_day), false)         as is_day_after_holiday
    from calendar

),

events as (

    select
        date_day,
        day_of_week,
        snowfall_cm,
        case
            when is_heavy_snow_day     then 'heavy_snow'
            when is_holiday            then 'holiday'
            when is_day_after_snow     then 'day_after_snow'
            when is_day_after_holiday  then 'day_after_holiday'
        end as disruption_reason
    from with_previous

)

select
    concat(cast(t.pickup_date as string), '-', t.license_num)        as metric_key,
    t.pickup_date,
    t.license_num,
    e.day_of_week,
    e.snowfall_cm,
    e.disruption_reason,
    e.disruption_reason is not null                                  as is_expected_disruption,

    t.nb_trips,
    t.nb_flagged_trips,
    t.nb_timeline_anomalies,
    t.nb_trips_with_cbd_fee,

    safe_divide(t.nb_flagged_trips, t.nb_trips)                      as share_flagged,
    safe_divide(t.nb_timeline_anomalies, t.nb_trips)                 as share_timeline_anomaly,
    safe_divide(t.nb_trips_with_cbd_fee, t.nb_trips)                 as share_cbd_fee,
    safe_divide(t.clean_driver_pay_usd, t.nb_clean_trips)            as avg_clean_driver_pay_usd,
    1 - safe_divide(t.clean_driver_pay_usd, t.clean_base_fare_usd)   as platform_margin_rate

from trips as t
join events as e
    on t.pickup_date = e.date_day