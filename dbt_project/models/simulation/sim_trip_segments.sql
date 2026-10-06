-- Segments de courses propres : la base de la simulation.
-- Les règles de bonus s'appliquent à ces segments, avec des sommes additives.
-- Au plus 2 x 2 x 24 x 2 x 2 x 2 = 768 lignes.

with zones as (

    select
        pickup_location_id,
        is_high_fee_zone
    from {{ ref('agg_zone_congestion') }}

)

select
    concat(
        f.license_num, '-',
        if(f.is_snowing, 'snow', 'dry'), '-',
        cast(f.pickup_hour as string), '-',
        if(f.is_weekend, 'we', 'wd'), '-',
        if(coalesce(z.is_high_fee_zone, false), 'hf', 'nhf'), '-',
        if(f.is_airport_trip, 'ap', 'nap')
    )                                         as segment_key,
    f.license_num,
    f.is_snowing,
    f.pickup_hour,
    f.is_weekend,
    coalesce(z.is_high_fee_zone, false)       as is_high_fee_zone,
    f.is_airport_trip,

    count(*)                                  as nb_trips,
    sum(f.driver_pay_usd)                     as driver_pay_usd,
    sum(f.base_passenger_fare_usd)            as base_fare_usd

from {{ ref('fct_trips') }} as f
left join zones as z
    on f.pickup_location_id = z.pickup_location_id
where f.is_clean_trip
group by 1, 2, 3, 4, 5, 6, 7