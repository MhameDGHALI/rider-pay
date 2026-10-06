-- À l'équilibre, le coût du bonus par course supplémentaire égale la marge par course :
-- bonus x (1 + L) / L = marge. Retourne les blocs où l'identité n'est pas vérifiée.
select
    block,
    bonus_usd,
    avg_margin_usd,
    break_even_lift,
    bonus_usd * (1 + break_even_lift) / break_even_lift as cost_per_extra_trip_usd
from {{ ref('exp_break_even') }}
where break_even_lift is not null
  and abs(bonus_usd * (1 + break_even_lift) / break_even_lift - avg_margin_usd) > 0.000001