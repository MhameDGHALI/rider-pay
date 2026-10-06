-- Test de régression de la règle des événements attendus : les trois jours de forte neige connus
-- (25 janvier, 22 et 23 février, au moins 8 cm de neige) doivent être reconnus.
-- Retourne les jours non reconnus.
select
    storm_day,
    m.disruption_reason
from unnest([date '2026-01-25', date '2026-02-22', date '2026-02-23']) as storm_day
left join (
    select distinct pickup_date, disruption_reason
    from {{ ref('dq_daily_metrics') }}
) as m
    on m.pickup_date = storm_day
where coalesce(m.disruption_reason, 'aucun') != 'heavy_snow'