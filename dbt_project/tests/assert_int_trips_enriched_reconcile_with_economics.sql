-- Réconciliation : les jointures ne doivent ni supprimer ni dupliquer de course.
-- Retourne une ligne (donc échoue) si le nombre de courses ou le total de driver_pay diffère.
with before_join as (
    select count(*) as n, sum(driver_pay_usd) as total
    from {{ ref('int_trip_economics') }}
),
after_join as (
    select count(*) as n, sum(driver_pay_usd) as total
    from {{ ref('int_trips_enriched') }}
)
select
    before_join.n      as rows_before,
    after_join.n       as rows_after,
    before_join.total  as driver_pay_before,
    after_join.total   as driver_pay_after
from before_join
cross join after_join
where before_join.n != after_join.n
   or abs(before_join.total - after_join.total) > 0.01