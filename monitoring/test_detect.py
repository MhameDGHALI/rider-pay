"""Tests du détecteur sur des données SIMULÉES, avec des anomalies injectées à des endroits connus.

Aucun accès à BigQuery. Lancer depuis la racine du projet : python monitoring/test_detect.py
Un test est réussi quand le script se termine sans erreur ("OK").
"""
import datetime as dt

import numpy as np
import pandas as pd

from detect import detect

LICENSES = ["HV0003", "HV0005"]
DOW_EFFECT = {1: -0.02, 2: -0.08, 3: -0.04, 4: 0.0, 5: 0.03, 6: 0.08, 7: 0.05}   # 1 = dimanche


def make_series(rng: np.random.Generator) -> pd.DataFrame:
    """59 jours x 2 opérateurs, avec un peu de bruit et aucune anomalie."""
    rows = []
    day = dt.date(2026, 1, 1)
    while day <= dt.date(2026, 2, 28):
        dow = (day.isoweekday() % 7) + 1                      # 1 = dimanche, 2 = lundi, ...
        for lic, base in (("HV0003", 150_000), ("HV0005", 58_000)):
            rows.append({
                "pickup_date": day, "license_num": lic, "day_of_week": dow,
                "is_expected_disruption": False, "disruption_reason": None,
                "nb_trips": base * np.exp(DOW_EFFECT[dow] + rng.normal(0, 0.06)),
                "avg_clean_driver_pay_usd": 20.2 * np.exp(rng.normal(0, 0.012)),
                "platform_margin_rate": 0.227 + rng.normal(0, 0.003),
                "share_flagged": 0.0029 + rng.normal(0, 0.0004),
                "share_timeline_anomaly": 0.018 + rng.normal(0, 0.0012),
                "share_cbd_fee": 0.315 + rng.normal(0, 0.006),
            })
        day += dt.timedelta(days=1)
    return pd.DataFrame(rows)


def inject(df: pd.DataFrame, date: dt.date, lic: str, metric: str, factor: float = None, add: float = None) -> pd.DataFrame:
    out = df.copy()
    mask = (out["pickup_date"] == date) & (out["license_num"] == lic)
    if factor is not None:
        out.loc[mask, metric] = out.loc[mask, metric] * factor
    if add is not None:
        out.loc[mask, metric] = out.loc[mask, metric] + add
    return out


def found(alerts: pd.DataFrame, date: dt.date, lic: str, metric: str) -> bool:
    if alerts.empty:
        return False
    return bool(((alerts["pickup_date"] == date) & (alerts["license_num"] == lic) & (alerts["metric"] == metric)).any())


def main() -> None:
    rng = np.random.default_rng(7)

    # 1. Une série saine ne doit presque jamais déclencher d'alerte
    n_alerts, n_series = 0, 200
    for _ in range(n_series):
        n_alerts += len(detect(make_series(rng)))
    per_series = n_alerts / n_series
    print(f"Série saine : {per_series:.2f} fausse(s) alerte(s) par série de 118 jours-opérateurs et 6 indicateurs")
    assert per_series < 0.5, "trop de fausses alertes"

    # 2. Des anomalies franches, injectées une par une, doivent être détectées
    base = make_series(rng)
    cases = [
        ("volume divisé par 2,5", dt.date(2026, 2, 10), "HV0003", "nb_trips", dict(factor=0.4)),
        ("rémunération moyenne +30 %", dt.date(2026, 1, 14), "HV0005", "avg_clean_driver_pay_usd", dict(factor=1.30)),
        ("part de courses signalées x10", dt.date(2026, 2, 3), "HV0003", "share_flagged", dict(factor=10)),
        ("marge de la plateforme -6 points", dt.date(2026, 1, 21), "HV0003", "platform_margin_rate", dict(add=-0.06)),
        ("chronologies incohérentes x4", dt.date(2026, 2, 17), "HV0005", "share_timeline_anomaly", dict(factor=4)),
        ("frais de congestion disparus", dt.date(2026, 1, 28), "HV0003", "share_cbd_fee", dict(add=-0.25)),
    ]
    for label, date, lic, metric, kw in cases:
        alerts = detect(inject(base, date, lic, metric, **kw))
        ok = found(alerts, date, lic, metric)
        print(f"  {'détectée ' if ok else 'MANQUÉE  '} {label}")
        assert ok, f"anomalie manquée : {label}"

    # 3. Une dérive minuscule ne doit pas déclencher d'alerte
    small = detect(inject(base, dt.date(2026, 2, 10), "HV0003", "nb_trips", factor=1.02))
    assert not found(small, dt.date(2026, 2, 10), "HV0003", "nb_trips"), "fausse alerte sur +2 %"
    print("  ignorée   volume +2 % (variation normale)")

    # 4. Un événement attendu est signalé en information, pas en alerte
    event = inject(base, dt.date(2026, 2, 23), "HV0003", "nb_trips", factor=0.15)
    event.loc[event["pickup_date"] == dt.date(2026, 2, 23), "is_expected_disruption"] = True
    alerts = detect(event)
    row = alerts[(alerts["pickup_date"] == dt.date(2026, 2, 23)) & (alerts["metric"] == "nb_trips")]
    assert not row.empty and (row["severity"] == "information").all()
    print("  information : un jour de tempête connu n'est pas une alerte")

    # 5. Un problème de qualité des données reste une alerte, même un jour de tempête
    quality = inject(base, dt.date(2026, 2, 23), "HV0003", "share_flagged", add=0.20)
    quality.loc[quality["pickup_date"] == dt.date(2026, 2, 23), "is_expected_disruption"] = True
    alerts = detect(quality)
    row = alerts[(alerts["pickup_date"] == dt.date(2026, 2, 23)) & (alerts["metric"] == "share_flagged")]
    assert not row.empty and (row["severity"] == "alerte").all()
    print("  alerte      une part de courses signalées anormale un jour de tempête reste une alerte")
    
    print("OK")


if __name__ == "__main__":
    main()