-- Une ligne par scénario : coût du bonus et comparaison avec la situation actuelle.
-- Coût STATIQUE : le comportement des chauffeurs est supposé inchangé.
-- Montants relatifs à l'échantillon de 30 % des courses.

with base as (

    select
        sum(nb_trips)        as nb_trips,
        sum(driver_pay_usd)  as baseline_pay_usd
    from {{ ref('sim_trip_segments') }}

),

bonus as (

    select
        scenario_id,
        sum(bonus_usd)  as bonus_usd,
        sum(nb_trips)   as nb_trips_with_bonus
    from {{ ref('sim_scenario_segment_bonus') }}
    group by scenario_id

)

select
    sc.scenario_id,
    sc.scenario_label,
    sc.is_baseline = 1                                                          as is_baseline,

    base.nb_trips                                                               as nb_trips,
    base.baseline_pay_usd                                                       as baseline_pay_usd,
    coalesce(bonus.bonus_usd, 0)                                                as bonus_usd,
    base.baseline_pay_usd + coalesce(bonus.bonus_usd, 0)                        as total_pay_usd,

    safe_divide(base.baseline_pay_usd + coalesce(bonus.bonus_usd, 0), base.nb_trips)
                                                                                as pay_per_trip_usd,
    safe_divide(coalesce(bonus.bonus_usd, 0), base.nb_trips)                    as bonus_per_trip_usd,
    safe_divide(coalesce(bonus.bonus_usd, 0), base.baseline_pay_usd)            as cost_increase_pct,

    coalesce(bonus.nb_trips_with_bonus, 0)                                      as nb_trips_with_bonus,
    safe_divide(coalesce(bonus.nb_trips_with_bonus, 0), base.nb_trips)          as share_trips_with_bonus

from {{ ref('sim_scenarios') }} as sc
cross join base
left join bonus
    on sc.scenario_id = bonus.scenario_id