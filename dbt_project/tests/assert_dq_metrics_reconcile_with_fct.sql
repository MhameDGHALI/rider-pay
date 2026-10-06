-- Réconciliation : les indicateurs quotidiens doivent retrouver exactement le nombre de courses
-- et le nombre de courses signalées de fct_trips.
with metrics as (
    select
        sum(nb_trips)          as nb_trips,
        sum(nb_flagged_trips)  as nb_flagged
    from {{ ref('dq_daily_metrics') }}
),
fct as (
    select
        count(*)                as nb_trips,
        countif(not is_clean_trip) as nb_flagged
    from {{ ref('fct_trips') }}
)
select
    metrics.nb_trips as metrics_trips,   fct.nb_trips as fct_trips,
    metrics.nb_flagged as metrics_flagged, fct.nb_flagged as fct_flagged
from metrics
cross join fct
where metrics.nb_trips != fct.nb_trips
   or metrics.nb_flagged != fct.nb_flagged