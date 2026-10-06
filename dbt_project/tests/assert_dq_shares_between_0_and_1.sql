-- Toute part doit être comprise entre 0 et 1. Retourne les lignes en erreur.
select metric_key, share_flagged, share_timeline_anomaly, share_cbd_fee
from {{ ref('dq_daily_metrics') }}
where share_flagged not between 0 and 1
   or share_timeline_anomaly not between 0 and 1
   or share_cbd_fee not between 0 and 1
   or share_flagged is null
   or share_timeline_anomaly is null
   or share_cbd_fee is null