-- Cohérence entre deux chemins de calcul : le coût de la grille au taux de la règle R_SNOW_15
-- doit égaler celui du scénario SNOW_15. Échoue aussi si la grille ne contient pas ce taux.
with scenario_side as (
    select bonus_usd as scenario_bonus
    from {{ ref('sim_scenario_comparison') }}
    where scenario_id = 'SNOW_15'
),
grid_side as (
    select bonus_usd as grid_bonus
    from {{ ref('sim_snow_sensitivity') }}
    where rate_pct = (
        select round(100 * bonus_value)
        from {{ ref('sim_rules') }}
        where rule_id = 'R_SNOW_15'
    )
)
select
    scenario_side.scenario_bonus,
    grid_side.grid_bonus
from scenario_side
left join grid_side on true
where grid_side.grid_bonus is null
   or abs(scenario_side.scenario_bonus - grid_side.grid_bonus) > 0.05