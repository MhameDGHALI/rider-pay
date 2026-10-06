-- Chaque jour perturbé doit correspondre à une unité par bloc (3 jours x 2 blocs = 6 unités).
-- Retourne une ligne (donc échoue) si une date du seed ne correspond à aucune unité (faute de frappe).
with expected as (
    select
        (select count(*) from {{ ref('exp_disturbed_dates') }})
      * (select count(*)
         from {{ ref('sim_rules') }}
         where rule_id in ('R_PEAK_AM', 'R_PEAK_PM')) as expected_units
),
actual as (
    select countif(is_disturbed_day) as actual_units
    from {{ ref('exp_switchback_assignment') }}
)
select
    expected.expected_units,
    actual.actual_units
from expected
cross join actual
where expected.expected_units != actual.actual_units