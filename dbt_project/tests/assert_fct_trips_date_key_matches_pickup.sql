-- La clé de partitionnement doit correspondre à la date réelle de prise en charge
-- et rester dans la plage de partitions définie (20260101 à 20260228).
-- Une valeur hors plage atterrirait dans une partition "poubelle". Retourne les lignes en erreur.
select trip_id, pickup_at, pickup_date_key
from {{ ref('fct_trips') }}
where pickup_date_key != cast(format_date('%Y%m%d', date(pickup_at)) as int64)
   or pickup_date_key not between 20260101 and 20260228