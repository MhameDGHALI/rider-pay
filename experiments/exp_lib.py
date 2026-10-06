"""Fonctions communes aux scripts d'analyse de l'expérience (jours 14 et 15).

- chargement des unités et de la répartition depuis BigQuery ;
- répartition au hasard stratifiée (même principe que le modèle dbt exp_switchback_assignment) ;
- régression de l'effet du traitement, avec intervalle de confiance.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05


def load_assignment() -> pd.DataFrame:
    """Lit les unités et leur répartition (test ou contrôle) dans BigQuery."""
    sys.path.append(str(ROOT / "ingestion"))
    from config import PROJECT_ID, check_project_id
    from google.cloud import bigquery

    check_project_id()
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        select unit_id, block, day_of_week, stratum, nb_trips, snow_hours, arm, is_disturbed_day
        from `{PROJECT_ID}.dbt_dev_experiments.exp_switchback_assignment`
        order by unit_id
    """
    df = client.query(sql).to_dataframe()
    df["arm_bin"] = (df["arm"] == "treatment").astype(int)
    df["is_disturbed_day"] = df["is_disturbed_day"].astype(bool)
    return df


def assign_stratified(strata: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Répartition au hasard DANS chaque strate : chaque strate est équilibrée (à une unité près)."""
    arm = np.zeros(len(strata), dtype=int)
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        rng.shuffle(idx)
        n_treat = len(idx) // 2 + (int(rng.integers(0, 2)) if len(idx) % 2 else 0)
        arm[idx[:n_treat]] = 1
    return arm


def fit_effect(y: np.ndarray, arm: np.ndarray, strata_dummies: np.ndarray, snow: np.ndarray) -> dict:
    """Régression de y sur le traitement, la strate et la neige (moindres carrés).

    Retourne l'effet du traitement (en points de logarithme), son erreur type, sa p-value et
    son intervalle de confiance à 95 % (loi de Student).
    """
    x = np.column_stack([arm, strata_dummies, snow])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    rank = np.linalg.matrix_rank(x)
    dof = len(y) - rank
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.pinv(x.T @ x)
    se = float(np.sqrt(cov[0, 0]))
    p_value = float(2 * stats.t.sf(abs(beta[0] / se), df=dof))
    t_crit = float(stats.t.ppf(1 - ALPHA / 2, df=dof))
    return {
        "beta": float(beta[0]),
        "se": se,
        "p": p_value,
        "ci_low": float(beta[0] - t_crit * se),
        "ci_high": float(beta[0] + t_crit * se),
        "dof": int(dof),
        "t_crit": t_crit,
    }


def design(df: pd.DataFrame):
    """Variables de la régression : log du nombre de courses, bras, strates (indicatrices), neige."""
    y = np.log(df["nb_trips"].to_numpy(dtype=float))
    arm = df["arm_bin"].to_numpy(dtype=float)
    dummies = pd.get_dummies(df["stratum"]).to_numpy(dtype=float)
    snow = df["snow_hours"].to_numpy(dtype=float)
    return y, arm, dummies, snow


def to_pct(log_points: float) -> float:
    """Convertit un effet en points de logarithme en pourcentage de variation."""
    return 100.0 * (np.exp(log_points) - 1.0)