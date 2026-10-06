-- Coût de chaque règle dans chaque scénario.
-- Une ligne par couple scénario - règle (seulement si la règle s'applique à au moins un segment).

with per_rule as (

    select
        concat(m.scenario_id, '|', r.rule_id)     as scenario_rule_key,
        m.scenario_id,
        r.rule_id,
        r.rule_label,
        sum({{ sim_bonus_amount('seg', 'r') }})   as bonus_usd,
        sum(seg.nb_trips)                         as nb_trips_matched

    from {{ ref('sim_scenario_rules') }} as m
    join {{ ref('sim_rules') }} as r
        on m.rule_id = r.rule_id
    cross join {{ ref('sim_trip_segments') }} as seg
    where {{ sim_rule_matches('seg', 'r') }}
    group by 1, 2, 3, 4

)

select
    scenario_rule_key,
    scenario_id,
    rule_id,
    rule_label,
    bonus_usd,
    nb_trips_matched,
    safe_divide(bonus_usd, nb_trips_matched)                              as bonus_per_matched_trip_usd,
    safe_divide(bonus_usd, sum(bonus_usd) over (partition by scenario_id)) as share_of_scenario_bonus
from per_rule