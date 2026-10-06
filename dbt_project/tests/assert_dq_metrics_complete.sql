-- Complétude : une ligne par jour du calendrier et par opérateur présent dans fct_trips.
-- Un jour sans aucune course ferait disparaître une ligne : le trou serait invisible pour un détecteur d'anomalies.
with expected as (
    select
        (select count(*) from {{ ref('dim_date') }})
      * (select count(distinct license_num) from {{ ref('fct_trips') }}) as expected_rows
),
actual as (
    select count(*) as actual_rows
    from {{ ref('dq_daily_metrics') }}
)
select
    expected.expected_rows,
    actual.actual_rows
from expected
cross join actual
where expected.expected_rows != actual.actual_rows