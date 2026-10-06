"""Jour 13 : test A/A sur les unités du switchback.

Un test A/A applique la méthode d'expérimentation SANS aucun effet : on répartit au hasard les unités
en "test" et "contrôle", puis on cherche une différence. Il ne doit pas y en avoir. On répète 2 000 fois
pour vérifier deux choses :
  1. le test se trompe environ 5 % du temps (taux de faux positifs attendu) ;
  2. à quel point la mesure est bruitée (écart-type de l'effet estimé), donc quel effet minimal détectable.

Entrée : BigQuery, table dbt_dev_experiments.exp_switchback_units (données réelles, aucun effet injecté).
Sorties : docs/aa_test_results.md et docs/img/aa_pvalues.png
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
N_SIM = 2000
ALPHA = 0.05
SEED = 42


def load_units() -> pd.DataFrame:
    """Lit les unités d'expérience dans BigQuery."""
    sys.path.append(str(ROOT / "ingestion"))
    from config import PROJECT_ID, check_project_id
    from google.cloud import bigquery

    check_project_id()
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        select unit_id, block, day_of_week, stratum, nb_trips, snow_hours
        from `{PROJECT_ID}.dbt_dev_experiments.exp_switchback_units`
        order by unit_id
    """
    return client.query(sql).to_dataframe()


def assign_complete(n: int, rng: np.random.Generator) -> np.ndarray:
    """Répartition au hasard sur toutes les unités : moitié test, moitié contrôle."""
    arm = np.array([1] * (n // 2) + [0] * (n - n // 2))
    rng.shuffle(arm)
    return arm


def assign_stratified(strata: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Répartition au hasard DANS chaque strate : chaque strate est équilibrée (à une unité près)."""
    arm = np.zeros(len(strata), dtype=int)
    for s in np.unique(strata):
        idx = np.where(strata == s)[0]
        rng.shuffle(idx)
        n_treat = len(idx) // 2 + (int(rng.integers(0, 2)) if len(idx) % 2 else 0)
        arm[idx[:n_treat]] = 1
    return arm


def naive_test(y: np.ndarray, arm: np.ndarray):
    """Différence de moyennes entre test et contrôle, avec un test de Student (variances inégales)."""
    effect = y[arm == 1].mean() - y[arm == 0].mean()
    p_value = stats.ttest_ind(y[arm == 1], y[arm == 0], equal_var=False).pvalue
    return effect, p_value


def adjusted_test(y: np.ndarray, arm: np.ndarray, strata_dummies: np.ndarray, snow: np.ndarray):
    """Régression de y sur le traitement, la strate et la neige : effet du traitement à strate et météo égales."""
    x = np.column_stack([arm, strata_dummies, snow])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    rank = np.linalg.matrix_rank(x)
    dof = len(y) - rank
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.pinv(x.T @ x)
    t_stat = beta[0] / np.sqrt(cov[0, 0])
    p_value = 2 * stats.t.sf(abs(t_stat), df=dof)
    return beta[0], p_value


def simulate(df: pd.DataFrame, n_sim: int = N_SIM, seed: int = SEED) -> dict:
    """Répète n_sim répartitions au hasard et calcule effet et p-value pour chaque méthode."""
    rng = np.random.default_rng(seed)
    y = np.log(df["nb_trips"].to_numpy(dtype=float))        # on travaille en logarithme : effet en %
    strata = df["stratum"].to_numpy()
    snow = df["snow_hours"].to_numpy(dtype=float)
    strata_dummies = pd.get_dummies(df["stratum"]).to_numpy(dtype=float)

    out = {key: {"effect": [], "p": []} for key in
           ["complet_simple", "complet_ajuste", "strat_simple", "strat_ajuste"]}

    for _ in range(n_sim):
        arm_c = assign_complete(len(df), rng)
        arm_s = assign_stratified(strata, rng)
        for key, arm, fn in [
            ("complet_simple", arm_c, lambda a: naive_test(y, a)),
            ("complet_ajuste", arm_c, lambda a: adjusted_test(y, a, strata_dummies, snow)),
            ("strat_simple", arm_s, lambda a: naive_test(y, a)),
            ("strat_ajuste", arm_s, lambda a: adjusted_test(y, a, strata_dummies, snow)),
        ]:
            effect, p_value = fn(arm)
            out[key]["effect"].append(effect)
            out[key]["p"].append(p_value)
    return out


def summarize(out: dict) -> pd.DataFrame:
    labels = {
        "complet_simple": "Répartition complète, différence simple",
        "complet_ajuste": "Répartition complète, régression (strate + neige)",
        "strat_simple": "Répartition par strate, différence simple",
        "strat_ajuste": "Répartition par strate, régression (strate + neige)",
    }
    rows = []
    for key, label in labels.items():
        effects = np.array(out[key]["effect"])
        p_values = np.array(out[key]["p"])
        sd = effects.std(ddof=1)
        rows.append({
            "méthode": label,
            "faux positifs (%)": round(100 * float((p_values < ALPHA).mean()), 1),
            "biais moyen (%)": round(100 * float(effects.mean()), 2),
            "écart-type de l'effet (%)": round(100 * float(sd), 2),
            "effet minimal détectable approx. (%)": round(100 * 2.8 * float(sd), 1),
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = load_units()
    print(f"{len(df)} unités, {df['stratum'].nunique()} strates")
    cv = df["nb_trips"].std() / df["nb_trips"].mean()
    print(f"Variation du nombre de courses entre unités : écart-type / moyenne = {cv:.1%}")
    print(df.groupby("block")["nb_trips"].agg(["count", "mean", "std"]).round(0))

    out = simulate(df)
    table = summarize(out)
    print("\nRésultats du test A/A (aucun effet injecté) :")
    print(table.to_string(index=False))

    docs = ROOT / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    lines = [
        "# Test A/A du switchback",
        "",
        f"{N_SIM} répartitions au hasard sur {len(df)} unités réelles, sans aucun effet injecté.",
        "Un test correct se trompe environ 5 % du temps et n'a pas de biais.",
        "",
        "| " + " | ".join(table.columns) + " |",
        "|" + "---|" * len(table.columns),
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    (docs / "aa_test_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), sharey=True)
    for ax, key, title in [(axes[0], "complet_simple", "Répartition complète, différence simple"),
                           (axes[1], "strat_ajuste", "Par strate, régression")]:
        ax.hist(out[key]["p"], bins=20, range=(0, 1), edgecolor="white")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("p-value")
    axes[0].set_ylabel("nombre de simulations")
    fig.suptitle("Test A/A : les p-values doivent être uniformes", fontsize=11)
    fig.tight_layout()
    fig.savefig(docs / "img" / "aa_pvalues.png", dpi=150)
    print("\nÉcrit : docs/aa_test_results.md et docs/img/aa_pvalues.png")


if __name__ == "__main__":
    main()