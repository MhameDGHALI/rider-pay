"""Détection d'anomalies sur les indicateurs quotidiens de santé des données.

Principe, pour chaque indicateur et chaque opérateur :
1. Valeur NORMALE d'un jour = médiane des AUTRES jours qui tombent le même jour de la semaine
   (un lundi se compare aux autres lundis). La médiane n'est presque pas influencée par les jours exceptionnels.
2. ÉCART du jour = valeur du jour - valeur normale.
3. ÉCHELLE = variation habituelle des écarts de tous les jours (écart absolu médian, MAD, multiplié par 1,4826 pour
   être comparable à un écart-type), avec un plancher : en dessous, un écart est jugé sans importance.
4. SCORE (z-score robuste) = écart / échelle. Une anomalie est un score de valeur absolue supérieure au seuil.

Un événement attendu (jour férié, forte neige, lendemain de l'un ou de l'autre) explique une variation de la DEMANDE
(volume, rémunération, marge, frais de congestion) : ces anomalies sont alors signalées à titre d'INFORMATION, pour ne
pas noyer les vraies alertes. Il n'explique PAS un problème de qualité des données (part de courses signalées,
chronologies incohérentes) : celles-ci restent des alertes, même un jour de tempête.
"""
import numpy as np
import pandas as pd

THRESHOLD = 4.0   # seuil du score ; calibré sur des séries simulées (environ 3 fausses alertes pour 100 mois de données)

# Indicateurs surveillés : passage au logarithme, plancher d'échelle (plus petit écart significatif), sens surveillé,
# et "muted" : vrai si un événement attendu (tempête, jour férié) peut expliquer l'anomalie (indicateur de demande)
METRICS = {
    "nb_trips":                 {"log": True,  "min_scale": 0.05,  "direction": "both", "muted": True,  "label": "nombre de courses"},
    "avg_clean_driver_pay_usd": {"log": True,  "min_scale": 0.02,  "direction": "both", "muted": True,  "label": "rémunération moyenne par course"},
    "platform_margin_rate":     {"log": False, "min_scale": 0.01,  "direction": "both", "muted": True,  "label": "marge de la plateforme"},
    "share_flagged":            {"log": False, "min_scale": 0.001, "direction": "up",   "muted": False, "label": "part de courses signalées"},
    "share_timeline_anomaly":   {"log": False, "min_scale": 0.003, "direction": "up",   "muted": False, "label": "part de chronologies incohérentes"},
    "share_cbd_fee":            {"log": False, "min_scale": 0.01,  "direction": "both", "muted": True,  "label": "part de courses avec frais de congestion"},
}


def robust_scores(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Valeur normale, échelle et score robuste de chaque ligne, pour un indicateur."""
    spec = METRICS[metric]
    x = df[metric].to_numpy(dtype=float)
    if spec["log"]:
        x = np.log(x)
    licenses = df["license_num"].to_numpy()
    key = pd.Series(licenses).astype(str).to_numpy() + "|" + df["day_of_week"].astype(str).to_numpy()

    normal = np.full(len(x), np.nan)
    for g in np.unique(key):
        idx = np.where(key == g)[0]
        if len(idx) < 4:                       # pas assez de jours comparables
            continue
        values = x[idx]
        for k, i in enumerate(idx):
            normal[i] = np.median(np.delete(values, k))     # médiane des autres jours
    deviation = x - normal

    scale = np.full(len(x), np.nan)
    for lic in np.unique(licenses):
        mask = licenses == lic
        d = deviation[mask]
        d = d[~np.isnan(d)]
        if len(d) == 0:
            continue
        mad = np.median(np.abs(d - np.median(d)))
        scale[mask] = max(1.4826 * mad, spec["min_scale"])
    return pd.DataFrame({"value": df[metric].to_numpy(), "normal": normal, "scale": scale,
                         "z": deviation / scale}, index=df.index)


def detect(df: pd.DataFrame, threshold: float = THRESHOLD) -> pd.DataFrame:
    """Retourne toutes les anomalies : une ligne par (jour, opérateur, indicateur) dont le score dépasse le seuil."""
    parts = []
    for metric, spec in METRICS.items():
        scores = robust_scores(df, metric)
        flagged = scores["z"] > threshold if spec["direction"] == "up" else scores["z"].abs() > threshold
        part = df.loc[flagged, ["pickup_date", "license_num", "is_expected_disruption", "disruption_reason"]].copy()
        part["metric"] = metric
        part["label"] = spec["label"]
        part["value"] = scores.loc[flagged, "value"]
        part["normal"] = np.exp(scores.loc[flagged, "normal"]) if spec["log"] else scores.loc[flagged, "normal"]
        part["z"] = scores.loc[flagged, "z"]
        part["muted"] = spec["muted"]
        parts.append(part)
    out = pd.concat(parts, ignore_index=True)
    if out.empty:
        return out
    out["severity"] = np.where(out["is_expected_disruption"] & out["muted"], "information", "alerte")
    return out.sort_values(["severity", "pickup_date", "license_num", "metric"]).reset_index(drop=True)


def format_message(alerts: pd.DataFrame) -> str:
    """Message court listant les alertes (les informations sont comptées, pas détaillées)."""
    if alerts.empty:
        return "Aucune anomalie de qualité des données."
    real = alerts[alerts["severity"] == "alerte"]
    info = int((alerts["severity"] == "information").sum())
    if real.empty:
        return f"Aucune alerte de qualité des données ({info} anomalie(s) expliquée(s) par un événement attendu)."
    lines = [f"{len(real)} alerte(s) de qualité des données :"]
    for _, r in real.iterrows():
        lines.append(f"- {r['pickup_date']} {r['license_num']} : {r['label']} = {r['value']:.4g} "
                     f"(normale {r['normal']:.4g}, score {r['z']:+.1f})")
    return "\n".join(lines)