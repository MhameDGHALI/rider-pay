-- Seuil de rentabilité du bonus de pointe, par bloc.
-- Population : les mêmes courses que les unités de l'expérience (courses propres, jours de semaine hors jours fériés,
-- heures des blocs lues dans les règles R_PEAK_AM et R_PEAK_PM).
-- Marge = tarif de base moins rémunération du chauffeur : APPROXIMATIVE (le tarif exclut taxes et frais).
-- Pour un bonus fixe c par course et une marge m par course, le bonus rapporte plus qu'il ne coûte
-- si le nombre de courses augmente de plus de c / (m - c). Le bonus est versé sur toutes les courses,
-- y compris les courses supplémentaires.

with blocks as (

    select
        case rule_id
            when 'R_PEAK_AM' then 'AM'
            when 'R_PEAK_PM' then 'PM'
        end          as block,
        hour_from,
        hour_to,
        bonus_value  as bonus_usd
    from {{ ref('sim_rules') }}
    where rule_id in ('R_PEAK_AM', 'R_PEAK_PM')
      and bonus_type = 'flat_per_trip'

),

trips as (

    select
        b.block,
        count(*)                       as nb_trips,
        avg(f.platform_margin_usd)     as avg_margin_usd,
        avg(f.driver_pay_usd)          as avg_driver_pay_usd
    from {{ ref('fct_trips') }} as f
    join blocks as b
        on f.pickup_hour between b.hour_from and b.hour_to
    where f.is_clean_trip
      and not f.is_weekend
      and f.pickup_date not in (select excluded_date from {{ ref('exp_excluded_dates') }})
    group by b.block

)

select
    b.block,
    b.bonus_usd,
    t.nb_trips,
    t.avg_margin_usd,
    t.avg_driver_pay_usd,
    case
        when t.avg_margin_usd > b.bonus_usd
            then safe_divide(b.bonus_usd, t.avg_margin_usd - b.bonus_usd)
    end as break_even_lift
from blocks as b
join trips as t
    on b.block = t.block