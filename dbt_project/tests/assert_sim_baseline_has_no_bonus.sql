-- La situation actuelle ne doit comporter aucun bonus. Retourne les lignes en erreur.
select scenario_id, bonus_usd
from {{ ref('sim_scenario_comparison') }}
where is_baseline
  and bonus_usd != 0