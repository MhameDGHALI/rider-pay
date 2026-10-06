-- Réconciliation par un troisième chemin : les courses des unités, plus celles des jours exclus,
-- doivent égaler les courses que le simulateur attribue au scénario PEAK_150.
with blocks as (
    select hour_from, hour_to
    from {{ ref('sim_rules') }}
    where rule_id in ('R_PEAK_AM', 'R_PEAK_PM')
),
units_total as (
    select sum(nb_trips) as n
    from {{ ref('exp_switchback_units') }}
),
excluded_total as (
    select count(*) as n
    from {{ ref('fct_trips') }} as f
    join blocks as b
        on f.pickup_hour between b.hour_from and b.hour_to
    where f.is_clean_trip
      and not f.is_weekend
      and f.pickup_date in (select excluded_date from {{ ref('exp_excluded_dates') }})
),
simulator_total as (
    select sum(nb_trips_matched) as n
    from {{ ref('sim_scenario_rule_bonus') }}
    where scenario_id = 'PEAK_150'
)
select
    units_total.n      as units_trips,
    excluded_total.n   as excluded_trips,
    simulator_total.n  as simulator_trips
from units_total
cross join excluded_total
cross join simulator_total
where units_total.n + excluded_total.n != simulator_total.n