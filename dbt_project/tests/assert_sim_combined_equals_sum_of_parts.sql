-- Les règles se cumulent et ne se recouvrent pas : le coût de COMBINED doit être la somme
-- des coûts de SNOW_15, PEAK_150 et ZONE_100.
select *
from (
    select
        sum(if(scenario_id = 'COMBINED', bonus_usd, 0))                              as combined_bonus,
        sum(if(scenario_id in ('SNOW_15', 'PEAK_150', 'ZONE_100'), bonus_usd, 0))    as parts_bonus
    from {{ ref('sim_scenario_comparison') }}
)
where abs(combined_bonus - parts_bonus) > 0.05