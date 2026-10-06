-- Répartition au hasard des unités entre test (treatment) et contrôle (control).
-- Aléatoire stratifiée : à l'intérieur de chaque strate (bloc x jour de la semaine), on classe les unités
-- par une empreinte (hachage) de leur identifiant et de la graine, puis on alterne test et contrôle.
-- Chaque strate est ainsi équilibrée à une unité près. Une strate de taille impaire donne son
-- unité en plus au test ou au contrôle selon un tirage propre à la strate (pas de biais systématique).
-- La répartition ne dépend d'aucun résultat : seuls l'identifiant et la graine interviennent.
-- is_disturbed_day marque les unités retirées de l'analyse de sensibilité (exploratoire).

with units as (

    select * from {{ ref('exp_switchback_units') }}

),

hashed as (

    select
        units.*,
        farm_fingerprint(concat('{{ var("exp_seed") }}', '|', unit_id))               as unit_hash,
        abs(mod(farm_fingerprint(concat('{{ var("exp_seed") }}', '|', stratum)), 2))  as stratum_flip
    from units

),

ranked as (

    select
        hashed.*,
        row_number() over (partition by stratum order by unit_hash) as rank_in_stratum
    from hashed

)

select
    unit_id,
    unit_date,
    block,
    day_of_week,
    stratum,
    nb_trips,
    driver_pay_usd,
    snow_hours,
    rank_in_stratum,
    if(mod(rank_in_stratum + stratum_flip, 2) = 1, 'treatment', 'control') as arm,
    unit_date in (select disturbed_date from {{ ref('exp_disturbed_dates') }}) as is_disturbed_day
from ranked