-- Réconciliation staging -> intermediate : même nombre de courses, même total de driver_pay.
-- Retourne une ligne (donc échoue) si un écart apparaît.
with stg_side as (
    select count(*) as n, sum(driver_pay_usd) as total
    from {{ ref('stg_hvfhv_trips') }}
),
int_side as (
    select count(*) as n, sum(driver_pay_usd) as total
    from {{ ref('int_trip_economics') }}
)
select
    stg_side.n      as stg_rows,
    int_side.n      as int_rows,
    stg_side.total  as stg_driver_pay,
    int_side.total  as int_driver_pay
from stg_side
cross join int_side
where stg_side.n != int_side.n
   or abs(stg_side.total - int_side.total) > 0.01