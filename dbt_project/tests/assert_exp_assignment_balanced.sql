-- Équilibre de la répartition : chaque strate doit avoir autant de test que de contrôle (à une unité près),
-- et la part globale de "treatment" doit rester entre 45 % et 55 %.
-- Retourne les cas en erreur.
with by_stratum as (
    select
        stratum,
        countif(arm = 'treatment') as n_treat,
        countif(arm = 'control')   as n_ctrl
    from {{ ref('exp_switchback_assignment') }}
    group by stratum
),
overall as (
    select safe_divide(countif(arm = 'treatment'), count(*)) as share_treat
    from {{ ref('exp_switchback_assignment') }}
)
select
    stratum,
    n_treat,
    n_ctrl,
    cast(null as float64) as share_treat
from by_stratum
where abs(n_treat - n_ctrl) > 1

union all

select
    'ALL'                  as stratum,
    cast(null as int64)    as n_treat,
    cast(null as int64)    as n_ctrl,
    share_treat
from overall
where share_treat < 0.45
   or share_treat > 0.55