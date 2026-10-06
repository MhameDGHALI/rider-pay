-- Part des courses avec frais de congestion, par zone de départ (toutes les courses).
-- is_high_fee_zone est une règle EMPIRIQUE : seuil et effectif minimal en variables dbt.
-- Ce n'est pas la définition officielle de la zone de réduction de la congestion.
select
    pickup_location_id,
    count(*)                                                    as nb_trips,
    countif(cbd_congestion_fee_usd > 0)                         as nb_trips_with_cbd_fee,
    safe_divide(countif(cbd_congestion_fee_usd > 0), count(*))  as share_trips_with_cbd_fee,
    (
        count(*) >= {{ var('congestion_zone_min_trips') }}
        and safe_divide(countif(cbd_congestion_fee_usd > 0), count(*))
            >= {{ var('congestion_zone_threshold') }}
    )                                                           as is_high_fee_zone
from {{ ref('fct_trips') }}
group by pickup_location_id