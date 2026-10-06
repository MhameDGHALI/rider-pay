-- Dimension des opérateurs HVFHS, à partir du seed operators (dictionnaire TLC).
select
    license_num,
    operator_name
from {{ ref('operators') }}