-- Réconciliation : la somme des coûts par règle doit égaler le coût de chaque scénario.
with by_rule as (
    select scenario_id, sum(bonus_usd) as bonus_usd
    from {{ ref('sim_scenario_rule_bonus') }}
    group by scenario_id
),
cmp as (
    select scenario_id, bonus_usd
    from {{ ref('sim_scenario_comparison') }}
    where not is_baseline
)
select
    cmp.scenario_id,
    cmp.bonus_usd       as comparison_bonus,
    by_rule.bonus_usd   as rule_bonus
from cmp
left join by_rule
    on cmp.scenario_id = by_rule.scenario_id
where by_rule.bonus_usd is null
   or abs(cmp.bonus_usd - by_rule.bonus_usd) > 0.05