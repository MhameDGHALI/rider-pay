"""Jour 14 : courbe de puissance par simulation.

Pour chaque effet vrai, quelle proportion d'expériences le détecte ? On répète 5 000 répartitions au hasard
(stratifiées), on injecte l'effet dans les unités test, on analyse avec la méthode retenue.

Astuce exacte : ajouter un effet constant c au logarithme des unités test décale l'effet estimé de c et ne change ni
son erreur type ni ses degrés de liberté. On calcule donc le bruit UNE fois par répartition, puis on déduit
la détection pour chaque effet.

Sorties : docs/power_curve.md et docs/img/power_curve.png
"""
import numpy as np
import pandas as pd
from scipy import stats

from exp_lib import ROOT, ALPHA, assign_stratified, design, fit_effect, load_assignment

N_SIM = 5000
SEED = 42
TAUS_PCT = np.arange(0, 32.5, 2.5)


def check_shortcut(y, strata_dummies, snow, strata, rng) -> None:
    """Vérifie par un calcul direct que l'astuce est exacte (effet injecté de 10 %)."""
    arm = assign_stratified(strata, rng).astype(float)
    base = fit_effect(y, arm, strata_dummies, snow)
    direct = fit_effect(y + arm * np.log(1.10), arm, strata_dummies, snow)
    assert np.isclose(direct["beta"], base["beta"] + np.log(1.10))
    assert np.isclose(direct["se"], base["se"])
    p_shift = 2 * stats.t.sf(abs((base["beta"] + np.log(1.10)) / base["se"]), df=base["dof"])
    assert np.isclose(direct["p"], p_shift)


def simulate(df: pd.DataFrame, rng: np.random.Generator) -> dict:
    """Pour chaque répartition, mémorise l'effet estimé sans effet injecté, l'erreur type et la valeur critique."""
    y, _, dummies, snow = design(df)
    strata = df["stratum"].to_numpy()
    check_shortcut(y, dummies, snow, strata, rng)
    betas, ses, tcrit = [], [], []
    for _ in range(N_SIM):
        arm = assign_stratified(strata, rng).astype(float)
        fit = fit_effect(y, arm, dummies, snow)
        betas.append(fit["beta"])
        ses.append(fit["se"])
        tcrit.append(fit["t_crit"])
    return {"beta": np.array(betas), "se": np.array(ses), "tcrit": np.array(tcrit)}


def power_table(sim: dict) -> pd.Series:
    """Puissance (proportion de détections) pour chaque effet vrai."""
    out = {}
    for tau in TAUS_PCT:
        shift = np.log(1 + tau / 100.0)
        detected = np.abs(sim["beta"] + shift) / sim["se"] > sim["tcrit"]
        out[float(tau)] = float(detected.mean())
    return pd.Series(out)


def mde(power: pd.Series, target: float = 0.8):
    """Plus petit effet (en %) dont la puissance atteint la cible, par interpolation."""
    taus, vals = power.index.to_numpy(), power.to_numpy()
    for i in range(1, len(taus)):
        if vals[i] >= target > vals[i - 1]:
            return float(taus[i - 1] + (target - vals[i - 1]) * (taus[i] - taus[i - 1]) / (vals[i] - vals[i - 1]))
    return None


def mean_estimate_if_detected(sim: dict, tau_pct: float):
    """Effet estimé moyen (en %) parmi les expériences qui détectent l'effet.

    Quand la puissance est faible, les expériences qui "réussissent" sont celles où le bruit a joué en faveur de l'effet :
    leur estimation surestime la vérité.
    """
    estimate = sim["beta"] + np.log(1 + tau_pct / 100.0)
    detected = np.abs(estimate) / sim["se"] > sim["tcrit"]
    if detected.sum() == 0:
        return None
    return float(100 * (np.exp(estimate[detected].mean()) - 1))


def units_needed(tau_pct: float, mean_se: float, n_units: int) -> float:
    """Ordre de grandeur du nombre d'unités pour 80 % de puissance.

    L'erreur type baisse comme 1 / racine du nombre d'unités : pour atteindre l'erreur type visée
    (effet / 2,8), il faut n_units x (erreur type actuelle / erreur type visée) au carré unités.
    Le bruit par unité est supposé inchangé.
    """
    target_se = np.log(1 + tau_pct / 100.0) / 2.8
    return n_units * (mean_se / target_se) ** 2


def main() -> None:
    df = load_assignment()
    rng = np.random.default_rng(SEED)
    analyses = {
        "Principale (toutes les unités)": df,
        "Sensibilité (sans jours perturbés, exploratoire)": df[~df["is_disturbed_day"]].reset_index(drop=True),
    }
    results, summary = {}, []
    for label, data in analyses.items():
        sim = simulate(data, rng)
        power = power_table(sim)
        results[label] = power
        mean_se = float(sim["se"].mean())
        summary.append({
            "analyse": label,
            "unités": len(data),
            "faux positifs (%)": round(100 * power.loc[0.0], 1),
            "erreur type moyenne (pts)": round(100 * mean_se, 2),
            "effet minimal détectable à 80 % (%)": None if mde(power) is None else round(mde(power), 1),
            "puissance à +5 % (%)": round(100 * float(np.interp(5, power.index, power.values)), 0),
            "puissance à +15 % (%)": round(100 * float(np.interp(15, power.index, power.values)), 0),
            "effet estimé moyen si détecté, vrai +5 % (%)": None if mean_estimate_if_detected(sim, 5) is None else round(mean_estimate_if_detected(sim, 5), 1),
            "effet estimé moyen si détecté, vrai +15 % (%)": None if mean_estimate_if_detected(sim, 15) is None else round(mean_estimate_if_detected(sim, 15), 1),
            "unités pour détecter +5 % (approx.)": int(round(units_needed(5, mean_se, len(data)))),
            "jours de semaine correspondants": int(round(units_needed(5, mean_se, len(data)) / 2)),
        })
    table = pd.DataFrame(summary)
    curve = pd.DataFrame({k: (100 * v).round(0) for k, v in results.items()})
    curve.index.name = "effet vrai (%)"
    print(table.to_string(index=False))
    print("\nPuissance (%) selon l'effet vrai :")
    print(curve.to_string())

    docs = ROOT / "docs"
    (docs / "img").mkdir(parents=True, exist_ok=True)
    cols = list(table.columns)
    lines = ["# Puissance par simulation", "",
             f"{N_SIM} répartitions au hasard (stratifiées) par analyse. Effet connu injecté dans les unités test.", "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in table.iterrows():
        lines.append("| " + " | ".join(str(v) for v in r.values) + " |")
    lines += ["", "Puissance (%) selon l'effet vrai :", "",
              "| effet vrai (%) | " + " | ".join(curve.columns) + " |", "|---|" + "---|" * len(curve.columns)]
    for tau, r in curve.iterrows():
        lines.append(f"| {tau:g} | " + " | ".join(f"{v:g}" for v in r.values) + " |")
    (docs / "power_curve.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    for label, power in results.items():
        ax.plot(power.index, 100 * power.values, marker="o", label=label)
    ax.axhline(80, color="grey", linestyle="--", linewidth=0.8)
    ax.axhline(5, color="grey", linestyle=":", linewidth=0.8)
    ax.set_xlabel("effet vrai du bonus sur le nombre de courses (%)")
    ax.set_ylabel("puissance (% d'expériences qui détectent l'effet)")
    ax.set_title("Courbe de puissance du switchback")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(docs / "img" / "power_curve.png", dpi=150)
    print("\nÉcrit : docs/power_curve.md et docs/img/power_curve.png")


if __name__ == "__main__":
    main()