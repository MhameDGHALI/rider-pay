"""Jour 14 : injection d'un effet connu et analyse complète sur la répartition réelle.

On ajoute un effet connu (en %) au nombre de courses des unités du bras test, puis on mesure cet effet avec la
méthode retenue (régression sur la strate et la neige). Comme on connaît la vérité, on vérifie que la méthode la retrouve.

Deux analyses : principale (toutes les unités) et de sensibilité (sans les jours perturbés, exploratoire).
Sorties : docs/effect_analysis.md et docs/img/effect_estimates.png
"""
import numpy as np
import pandas as pd
from scipy import stats

from exp_lib import ROOT, design, fit_effect, load_assignment, to_pct

EFFECTS_PCT = [0, 5, 15, 25]


def srm_and_balance(df: pd.DataFrame) -> None:
    """Contrôle de la répartition : tailles des bras (SRM) et équilibre des covariables."""
    n_t = int((df["arm"] == "treatment").sum())
    n_c = int((df["arm"] == "control").sum())
    p_srm = stats.chisquare([n_t, n_c]).pvalue
    print(f"Répartition : {n_t} test et {n_c} contrôle ; test du chi-deux contre 50/50 : p = {p_srm:.2f}")
    print("Neige moyenne (heures par bloc) : ",
          df.groupby("arm")["snow_hours"].mean().round(2).to_dict())
    print("Unités par strate et par bras :")
    print(df.groupby(["stratum", "arm"]).size().unstack().to_string())


def analyze(df: pd.DataFrame, tau_pct: float) -> dict:
    """Injecte l'effet tau_pct dans les unités test puis estime l'effet."""
    y, arm, dummies, snow = design(df)
    y_obs = y + arm * np.log(1 + tau_pct / 100.0)       # l'effet connu est ajouté au logarithme
    fit = fit_effect(y_obs, arm, dummies, snow)
    return {
        "effet vrai (%)": tau_pct,
        "effet estimé (%)": round(to_pct(fit["beta"]), 1),
        "IC 95 % bas (%)": round(to_pct(fit["ci_low"]), 1),
        "IC 95 % haut (%)": round(to_pct(fit["ci_high"]), 1),
        "p-value": round(fit["p"], 3),
        "détecté (p < 0,05)": "oui" if fit["p"] < 0.05 else "non",
        "l'IC contient le vrai effet": "oui" if fit["ci_low"] <= np.log(1 + tau_pct / 100.0) <= fit["ci_high"] else "non",
        "unités": len(df),
        "erreur type (pts)": round(100 * fit["se"], 2),
    }


def main() -> None:
    df = load_assignment()
    print(f"{len(df)} unités, dont {int(df['is_disturbed_day'].sum())} sur des jours perturbés")
    srm_and_balance(df)

    rows = []
    for label, data in [("Principale (toutes les unités)", df),
                        ("Sensibilité (sans jours perturbés, exploratoire)", df[~df["is_disturbed_day"]].reset_index(drop=True))]:
        for tau in EFFECTS_PCT:
            row = analyze(data, tau)
            row = {"analyse": label, **row}
            rows.append(row)
    table = pd.DataFrame(rows)
    print("\n" + table.to_string(index=False))

    docs = ROOT / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    cols = list(table.columns)
    lines = ["# Analyse des effets injectés", "",
             "Effet connu ajouté au nombre de courses des unités du bras test, puis mesuré par régression",
             "(strate + neige) sur la répartition réelle.", "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in table.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    (docs / "effect_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharex=True)
    for ax, (label, sub) in zip(axes, table.groupby("analyse", sort=False)):
        ypos = np.arange(len(sub))
        est = sub["effet estimé (%)"].to_numpy()
        low = est - sub["IC 95 % bas (%)"].to_numpy()
        high = sub["IC 95 % haut (%)"].to_numpy() - est
        ax.errorbar(est, ypos, xerr=[low, high], fmt="o", capsize=4)
        ax.scatter(sub["effet vrai (%)"], ypos, marker="|", s=300, color="red", label="effet vrai")
        ax.axvline(0, color="grey", linewidth=0.8)
        ax.set_yticks(ypos)
        ax.set_yticklabels([f"vrai +{int(t)} %" for t in sub["effet vrai (%)"]])
        ax.set_title(label, fontsize=9)
        ax.set_xlabel("effet estimé (%) et intervalle de confiance à 95 %")
    axes[0].legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(docs / "img" / "effect_estimates.png", dpi=150)
    print("\nÉcrit : docs/effect_analysis.md et docs/img/effect_estimates.png")


if __name__ == "__main__":
    main()