-- Le bonus neige doit être proportionnel au taux : le coût de SNOW_165 divisé par celui de SNOW_15
-- doit égaler 0,165 / 0,15 (valeurs lues dans le seed, pas écrites en dur).
with s15 as (
    select bonus_usd
    from {{ ref('sim_scenario_comparison') }}
    where scenario_id = 'SNOW_15'
),
s165 as (
    select bonus_usd
    from {{ ref('sim_scenario_comparison') }}
    where scenario_id = 'SNOW_165'
),
rates as (
    select
        (select bonus_value from {{ ref('sim_rules') }} where rule_id = 'R_SNOW_165')
      / (select bonus_value from {{ ref('sim_rules') }} where rule_id = 'R_SNOW_15') as expected_ratio
)
select
    s15.bonus_usd                                  as bonus_15,
    s165.bonus_usd                                 as bonus_165,
    rates.expected_ratio                           as expected_ratio,
    safe_divide(s165.bonus_usd, s15.bonus_usd)     as observed_ratio
from s15
cross join s165
cross join rates
where coalesce(s15.bonus_usd, 0) = 0
   or abs(safe_divide(s165.bonus_usd, s15.bonus_usd) - rates.expected_ratio) > 0.000001