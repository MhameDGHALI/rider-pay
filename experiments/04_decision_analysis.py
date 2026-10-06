"""Jour 15 : coût par course supplémentaire, seuil de rentabilité et règle de décision.

1. Seuil de rentabilité : avec un bonus fixe c par course et une marge moyenne m par course, le bonus rapporte plus
   qu'il ne coûte si le nombre de courses augmente de plus de L* = c / (m - c).
2. Règle de décision (fixée à l'avance) :
   - adopter si la borne BASSE de l'intervalle de confiance à 95 % de l'effet dépasse L* ;
   - abandonner si la borne HAUTE est sous L* ;
   - sinon : non concluant (prolonger l'expérience).
3. On l'applique aux effets injectés (répartition réelle), puis on estime sur 5 000 répartitions la probabilité de chaque
   décision selon l'effet vrai.

Entrée : BigQuery, table dbt_dev_experiments.exp_break_even et la répartition (exp_switchback_assignment).
Sorties : docs/decision_analysis.md et docs/img/decision_probabilities.png
"""
import sys

import numpy as np
import pandas as pd

from exp_lib import ROOT, assign_stratified, design, fit_effect, load_assignment, to_pct

EFFECTS_PCT = [0, 5, 15, 25]
GRID_PCT = [0, 10, 20, 30, 40, 50, 60, 70]
N_SIM = 5000
SEED = 42


def load_break_even() -> pd.DataFrame:
    """Lit la marge moyenne et le bonus de chaque bloc dans BigQuery."""
    sys.path.append(str(ROOT / "ingestion"))
    from config import PROJECT_ID, check_project_id
    from google.cloud import bigquery

    check_project_id()
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        select block, bonus_usd, nb_trips, avg_margin_usd
        from `{PROJECT_ID}.dbt_dev_experiments.exp_break_even`
        order by block
    """
    return client.query(sql).to_dataframe()


def break_even(be: pd.DataFrame) -> dict:
    """Bonus moyen c, marge moyenne m (pondérées par le nombre de courses) et seuil de rentabilité L* (en %)."""
    c = float(np.average(be["bonus_usd"], weights=be["nb_trips"]))
    m = float(np.average(be["avg_margin_usd"], weights=be["nb_trips"]))
    l_star = 100 * c / (m - c) if m > c else float("inf")
    return {"c": c, "m": m, "l_star_pct": l_star}


def cost_per_extra_trip(c: float, lift_pct: float) -> float:
    """Coût du bonus par course supplémentaire : le bonus est versé sur toutes les courses, y compris les nouvelles."""
    lift = lift_pct / 100.0
    return c * (1 + lift) / lift


def decide(ci_low_pct: float, ci_high_pct: float, l_star_pct: float) -> str:
    if ci_low_pct > l_star_pct:
        return "adopter"
    if ci_high_pct < l_star_pct:
        return "abandonner"
    return "non concluant"


def actual_draw(df: pd.DataFrame, l_star: float) -> list:
    """Applique la règle de décision aux effets injectés, sur la répartition réelle."""
    y, arm, dummies, snow = design(df)
    rows = []
    for tau in EFFECTS_PCT:
        fit = fit_effect(y + arm * np.log(1 + tau / 100.0), arm, dummies, snow)
        low, high = to_pct(fit["ci_low"]), to_pct(fit["ci_high"])
        decision = decide(low, high, l_star)
        truth = "adopter" if tau > l_star else "abandonner"
        verdict = "non concluant" if decision == "non concluant" else ("correcte" if decision == truth else "ERREUR")
        rows.append({"effet vrai (%)": tau, "effet estimé (%)": round(to_pct(fit["beta"]), 1),
                     "IC 95 % bas (%)": round(low, 1), "IC 95 % haut (%)": round(high, 1),
                     "décision": decision, "bonne décision": truth, "verdict": verdict})
    return rows


def decision_probabilities(df: pd.DataFrame, l_star: float, rng: np.random.Generator) -> pd.DataFrame:
    """Probabilité de chaque décision selon l'effet vrai (même astuce exacte que le jour 14)."""
    y, _, dummies, snow = design(df)
    strata = df["stratum"].to_numpy()
    betas, ses, tcrit = [], [], []
    for _ in range(N_SIM):
        arm = assign_stratified(strata, rng).astype(float)
        fit = fit_effect(y, arm, dummies, snow)
        betas.append(fit["beta"]); ses.append(fit["se"]); tcrit.append(fit["t_crit"])
    betas, ses, tcrit = np.array(betas), np.array(ses), np.array(tcrit)
    rows = []
    for tau in GRID_PCT:
        est = betas + np.log(1 + tau / 100.0)
        low, high = 100 * (np.exp(est - tcrit * ses) - 1), 100 * (np.exp(est + tcrit * ses) - 1)
        rows.append({"effet vrai (%)": tau,
                     "abandonner (%)": round(100 * float((high < l_star).mean()), 1),
                     "non concluant (%)": round(100 * float(((low <= l_star) & (high >= l_star)).mean()), 1),
                     "adopter (%)": round(100 * float((low > l_star).mean()), 1)})
    return pd.DataFrame(rows)


def md_table(table: pd.DataFrame) -> list:
    cols = list(table.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in table.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return lines


def main() -> None:
    be = load_break_even()
    res = break_even(be)
    c, m, l_star = res["c"], res["m"], res["l_star_pct"]
    print(be.to_string(index=False))
    print(f"\nBonus c = {c:.2f} $, marge moyenne m = {m:.2f} $, seuil de rentabilité L* = {l_star:.1f} %")

    lifts = [2.5, 5, 10, 15, 20, 25, 30, round(l_star, 1), 40, 50]
    cost = pd.DataFrame({"hausse du nombre de courses (%)": lifts,
                         "coût du bonus par course supplémentaire ($)": [round(cost_per_extra_trip(c, x), 2) for x in lifts]})
    print("\n" + cost.to_string(index=False))

    df = load_assignment()
    analyses = {"Principale (toutes les unités)": df,
                "Sensibilité (sans jours perturbés, exploratoire)": df[~df["is_disturbed_day"]].reset_index(drop=True)}
    draw_rows, prob_tables = [], {}
    rng = np.random.default_rng(SEED)
    for label, data in analyses.items():
        for row in actual_draw(data, l_star):
            draw_rows.append({"analyse": label, **row})
        prob_tables[label] = decision_probabilities(data, l_star, rng)
    draw = pd.DataFrame(draw_rows)
    print("\n" + draw.to_string(index=False))
    for label, table in prob_tables.items():
        print(f"\nProbabilité de chaque décision - {label}\n" + table.to_string(index=False))

    docs = ROOT / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    lines = ["# Seuil de rentabilité et règle de décision", "",
             f"Bonus c = {c:.2f} $ par course, marge moyenne m = {m:.2f} $ par course (tarif de base moins rémunération, approximative).",
             f"Seuil de rentabilité : L* = c / (m - c) = {l_star:.1f} % de courses en plus.", "",
             "## Coût du bonus par course supplémentaire", ""] + md_table(cost) + \
            ["", "## Règle de décision appliquée aux effets injectés (répartition réelle)", ""] + md_table(draw)
    for label, table in prob_tables.items():
        lines += ["", f"## Probabilité de chaque décision : {label}", ""] + md_table(table)
    (docs / "decision_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, (label, table) in zip(axes, prob_tables.items()):
        x = np.arange(len(table))
        ax.bar(x, table["abandonner (%)"], label="abandonner", color="#c0504d")
        ax.bar(x, table["non concluant (%)"], bottom=table["abandonner (%)"], label="non concluant", color="#bfbfbf")
        ax.bar(x, table["adopter (%)"], bottom=table["abandonner (%)"] + table["non concluant (%)"], label="adopter", color="#4f81bd")
        ax.set_xticks(x)
        ax.set_xticklabels(table["effet vrai (%)"])
        ax.set_xlabel(f"effet vrai du bonus (%), seuil de rentabilité {l_star:.0f} %")
        ax.set_title(label, fontsize=9)
    axes[0].set_ylabel("probabilité de la décision (%)")
    axes[0].legend(fontsize=8, loc="center left")
    fig.tight_layout()
    fig.savefig(docs / "img" / "decision_probabilities.png", dpi=150)
    print("\nÉcrit : docs/decision_analysis.md et docs/img/decision_probabilities.png")


if __name__ == "__main__":
    main()