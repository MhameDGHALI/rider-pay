-- Complétude : il doit y avoir une unité par jour de semaine non exclu et par bloc.
-- Retourne une ligne (donc échoue) si le nombre d'unités ne correspond pas au calendrier.
with expected as (
    select
        count(*) * (
            select count(*)
            from {{ ref('sim_rules') }}
            where rule_id in ('R_PEAK_AM', 'R_PEAK_PM')
        ) as expected_units
    from {{ ref('dim_date') }}
    where not is_weekend
      and date_day not in (select excluded_date from {{ ref('exp_excluded_dates') }})
),
actual as (
    select count(*) as actual_units
    from {{ ref('exp_switchback_units') }}
)
select
    expected.expected_units,
    actual.actual_units
from expected
cross join actual
where expected.expected_units != actual.actual_units