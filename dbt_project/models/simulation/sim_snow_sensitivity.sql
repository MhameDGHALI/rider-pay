-- Analyse de sensibilité du bonus neige : coût pour une série de taux (0 à 30 %, par pas de 5 points).
-- Le moteur de règles (macros) est réutilisé : on prend la règle R_SNOW_15 et on remplace son taux
-- par chaque valeur de la grille.

with grid as (

    select
        rate_pct,
        rate_pct / 100.0 as bonus_value
    from unnest(generate_array(0, 30, 5)) as rate_pct

),

rule_variants as (

    select
        base_rule.* except (bonus_value),
        grid.rate_pct,
        grid.bonus_value
    from {{ ref('sim_rules') }} as base_rule
    cross join grid
    where base_rule.rule_id = 'R_SNOW_15'

),

totals as (

    select
        sum(nb_trips)        as nb_trips,
        sum(driver_pay_usd)  as baseline_pay_usd
    from {{ ref('sim_trip_segments') }}

),

costs as (

    select
        rv.rate_pct,
        sum({{ sim_bonus_amount('seg', 'rv') }})  as bonus_usd,
        sum(seg.nb_trips)                         as nb_trips_with_bonus
    from rule_variants as rv
    cross join {{ ref('sim_trip_segments') }} as seg
    where {{ sim_rule_matches('seg', 'rv') }}
    group by rv.rate_pct

)

select
    grid.rate_pct,
    coalesce(costs.bonus_usd, 0)                                          as bonus_usd,
    coalesce(costs.nb_trips_with_bonus, 0)                                as nb_trips_with_bonus,
    safe_divide(coalesce(costs.bonus_usd, 0), totals.nb_trips)            as bonus_per_trip_usd,
    safe_divide(coalesce(costs.bonus_usd, 0), totals.baseline_pay_usd)    as cost_increase_pct,
    coalesce(costs.bonus_usd, 0)
        - lag(coalesce(costs.bonus_usd, 0)) over (order by grid.rate_pct) as step_cost_usd

from grid
cross join totals
left join costs
    on grid.rate_pct = costs.rate_pct