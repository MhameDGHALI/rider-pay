"""Jour 17 : sensibilité de l'alerte, mesurée en injectant des anomalies de tailles connues dans les VRAIS indicateurs.

Pour chaque indicateur et chaque taille d'anomalie, on choisit au hasard un jour ordinaire et un opérateur, on y injecte
l'anomalie (dans le sens qui dégrade la donnée), on relance la détection sur l'ensemble et on regarde si une alerte
est levée sur ce jour, cet opérateur et cet indicateur. On répète N_REP fois.

C'est l'équivalent, pour l'alerte, de la courbe de puissance de l'expérimentation : quelle proportion des anomalies
d'une taille donnée est détectée ?

Lancer depuis la racine du projet :  python monitoring/evaluate_detector.py
Sortie : docs/detector_evaluation.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from detect import METRICS, THRESHOLD, detect
from run_checks import load_metrics

ROOT = Path(__file__).resolve().parents[1]
N_REP = 60
SEED = 42

# Pour chaque indicateur : type d'injection (factor = multiplication, add = ajout), tailles, et libellé de chaque taille
INJECTIONS = {
    "nb_trips": ("factor", [0.9, 0.8, 0.7, 0.5], ["-10 %", "-20 %", "-30 %", "-50 %"]),
    "avg_clean_driver_pay_usd": ("factor", [1.02, 1.05, 1.10, 1.25], ["+2 %", "+5 %", "+10 %", "+25 %"]),
    "platform_margin_rate": ("add", [-0.01, -0.02, -0.04, -0.08], ["-1 pt", "-2 pts", "-4 pts", "-8 pts"]),
    "share_flagged": ("add", [0.002, 0.005, 0.01, 0.05], ["+0,2 pt", "+0,5 pt", "+1 pt", "+5 pts"]),
    "share_timeline_anomaly": ("add", [0.005, 0.01, 0.02, 0.05], ["+0,5 pt", "+1 pt", "+2 pts", "+5 pts"]),
    "share_cbd_fee": ("add", [-0.02, -0.05, -0.10, -0.20], ["-2 pts", "-5 pts", "-10 pts", "-20 pts"]),
}


def is_detected(alerts: pd.DataFrame, date, lic: str, metric: str) -> bool:
    if alerts.empty:
        return False
    mask = ((alerts["pickup_date"] == date) & (alerts["license_num"] == lic)
            & (alerts["metric"] == metric) & (alerts["severity"] == "alerte"))
    return bool(mask.any())


def main() -> None:
    df = load_metrics()
    rng = np.random.default_rng(SEED)
    baseline = detect(df)
    flagged_keys = set() if baseline.empty else set(zip(baseline["pickup_date"], baseline["license_num"], baseline["metric"]))
    ordinary = df[~df["is_expected_disruption"]].reset_index(drop=True)
    print(f"{len(df)} lignes, dont {len(ordinary)} jours ordinaires ; {len(baseline)} anomalie(s) déjà détectée(s) sur les données réelles")

    rows = []
    for metric, (kind, sizes, labels) in INJECTIONS.items():
        candidates = [i for i in range(len(ordinary))
                      if (ordinary.loc[i, "pickup_date"], ordinary.loc[i, "license_num"], metric) not in flagged_keys]
        for size, label in zip(sizes, labels):
            hits = 0
            for _ in range(N_REP):
                i = int(rng.choice(candidates))
                date, lic = ordinary.loc[i, "pickup_date"], ordinary.loc[i, "license_num"]
                mask = (df["pickup_date"] == date) & (df["license_num"] == lic)
                modified = df.copy()
                modified.loc[mask, metric] = modified.loc[mask, metric] * size if kind == "factor" else modified.loc[mask, metric] + size
                hits += is_detected(detect(modified), date, lic, metric)
            rows.append({"indicateur": METRICS[metric]["label"], "anomalie injectée": label,
                         "détectée (%)": round(100 * hits / N_REP)})
    table = pd.DataFrame(rows)

    pivot = table.pivot_table(index="indicateur", columns="anomalie injectée", values="détectée (%)", sort=False)
    ordered = []
    for metric, (_, _, labels) in INJECTIONS.items():
        ordered.append((METRICS[metric]["label"], labels))
    print("\nProportion d'anomalies détectées (%), selon la taille injectée :")
    for name, labels in ordered:
        cells = "   ".join(f"{lab}: {int(pivot.loc[name, lab]):>3} %" for lab in labels)
        print(f"  {name:<46} {cells}")

    lines = ["# Sensibilité du détecteur", "",
             f"{N_REP} anomalies injectées par indicateur et par taille, sur des jours ordinaires des vraies données ; seuil {THRESHOLD}.",
             "Une anomalie est « détectée » si une alerte est levée sur le bon jour, le bon opérateur et le bon indicateur.", "",
             "| indicateur | " + " | ".join(f"taille {i + 1}" for i in range(4)) + " |", "|---|---|---|---|---|"]
    for name, labels in ordered:
        lines.append(f"| {name} | " + " | ".join(f"{lab} : {int(pivot.loc[name, lab])} %" for lab in labels) + " |")
    lines += ["", "Les anomalies sont injectées dans le sens qui dégrade la donnée, une à la fois, sur un seul jour.",
              "Une dérive lente qui toucherait tous les jours n'est pas testée."]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "detector_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nÉcrit : docs/detector_evaluation.md")


if __name__ == "__main__":
    main()