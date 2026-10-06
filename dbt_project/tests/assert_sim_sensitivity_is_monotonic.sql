-- Un taux plus élevé ne peut pas coûter moins cher. Retourne les paliers en erreur.
select rate_pct, bonus_usd, previous_bonus_usd
from (
    select
        rate_pct,
        bonus_usd,
        lag(bonus_usd) over (order by rate_pct) as previous_bonus_usd
    from {{ ref('sim_snow_sensitivity') }}
)
where previous_bonus_usd is not null
  and bonus_usd < previous_bonus_usd