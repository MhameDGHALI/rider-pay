-- Réconciliation source -> staging : même nombre de courses, même total de driver_pay.
-- Retourne une ligne (donc échoue) si un écart apparaît. Tolérance de 0,01 $ sur la somme
-- car l'addition de nombres décimaux peut varier très légèrement selon l'ordre de calcul.
with raw_side as (
    select count(*) as n, sum(driver_pay) as total
    from {{ source('raw', 'hvfhv_trips') }}
),
stg_side as (
    select count(*) as n, sum(driver_pay_usd) as total
    from {{ ref('stg_hvfhv_trips') }}
)
select
    raw_side.n      as raw_rows,
    stg_side.n      as stg_rows,
    raw_side.total  as raw_driver_pay,
    stg_side.total  as stg_driver_pay
from raw_side
cross join stg_side
where raw_side.n != stg_side.n
   or abs(raw_side.total - stg_side.total) > 0.01