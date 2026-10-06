{{ config(severity='warn') }}
-- Rémunérations négatives. Échoue si au moins une ligne.
select trip_id, driver_pay_usd
from {{ ref('stg_hvfhv_trips') }}
where driver_pay_usd < 0