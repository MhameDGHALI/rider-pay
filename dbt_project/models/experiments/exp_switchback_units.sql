-- Unités de l'expérience switchback "bonus de pointe en semaine".
-- Une unité = un jour de semaine (hors jours fériés) x un bloc de pointe (matin ou soir).
-- Les blocs d'heures sont lus dans le seed sim_rules (règles R_PEAK_AM et R_PEAK_PM) :
-- une seule source de vérité pour le simulateur et pour l'expérience.
-- Les mesures sont réelles (courses propres). Aucun effet n'est injecté ici.

with blocks as (

    select
        case rule_id
            when 'R_PEAK_AM' then 'AM'
            when 'R_PEAK_PM' then 'PM'
        end as block,
        hour_from,
        hour_to
    from {{ ref('sim_rules') }}
    where rule_id in ('R_PEAK_AM', 'R_PEAK_PM')

),

trips as (

    select
        f.pickup_date,
        b.block,
        count(*)                 as nb_trips,
        sum(f.driver_pay_usd)    as driver_pay_usd
    from {{ ref('fct_trips') }} as f
    join blocks as b
        on f.pickup_hour between b.hour_from and b.hour_to
    where f.is_clean_trip
      and not f.is_weekend
      and f.pickup_date not in (select excluded_date from {{ ref('exp_excluded_dates') }})
    group by 1, 2

),

snow as (

    select
        date(w.observed_at)   as pickup_date,
        b.block,
        countif(w.is_snowing) as snow_hours
    from {{ ref('dim_weather_hour') }} as w
    join blocks as b
        on extract(hour from w.observed_at) between b.hour_from and b.hour_to
    group by 1, 2

)

select
    concat(cast(t.pickup_date as string), '-', t.block)                          as unit_id,
    t.pickup_date                                                                as unit_date,
    t.block,
    extract(dayofweek from t.pickup_date)                                        as day_of_week,
    concat(t.block, '-', cast(extract(dayofweek from t.pickup_date) as string))  as stratum,
    t.nb_trips,
    t.driver_pay_usd,
    coalesce(s.snow_hours, 0)                                                    as snow_hours
from trips as t
left join snow as s
    on t.pickup_date = s.pickup_date
   and t.block = s.block