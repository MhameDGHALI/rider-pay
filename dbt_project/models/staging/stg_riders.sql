-- Staging riders (table SYNTHETIQUE) : renommage et typage uniquement.
select
    cast(rider_id as int64)      as rider_id,
    hvfhs_license_num            as license_num,
    tier                         as rider_tier,
    cast(tenure_months as int64) as tenure_months,
    cast(signup_date as date)    as signup_date
from {{ source('raw', 'riders_synthetic') }}