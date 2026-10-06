-- Bonus simulé par scénario et par segment.
-- Les règles d'un même scénario se cumulent. Un bonus en pourcentage s'applique
-- à la rémunération réelle (pas de composition entre règles).

select
    concat(m.scenario_id, '|', seg.segment_key)   as scenario_segment_key,
    m.scenario_id,
    seg.segment_key,
    seg.nb_trips,
    seg.driver_pay_usd,
    sum({{ sim_bonus_amount('seg', 'r') }})       as bonus_usd,
    count(*)                                      as nb_rules_matched

from {{ ref('sim_scenario_rules') }} as m
join {{ ref('sim_rules') }} as r
    on m.rule_id = r.rule_id
cross join {{ ref('sim_trip_segments') }} as seg
where {{ sim_rule_matches('seg', 'r') }}
group by 1, 2, 3, 4, 5