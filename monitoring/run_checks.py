"""Contrôle de santé des données : lit les indicateurs quotidiens dans BigQuery, détecte les anomalies,
applique le journal des alertes acquittées, affiche, écrit un rapport et envoie le message.

Lancer depuis la racine du projet :  python monitoring/run_checks.py
Option : --fail  quitte avec un code d'erreur s'il reste au moins une alerte OUVERTE (utile pour une exécution automatique).

Entrée : BigQuery, table dbt_dev_monitoring.dq_daily_metrics, et monitoring/acknowledged_alerts.csv
Sortie : docs/data_health_report.md
"""
import sys
from pathlib import Path

import pandas as pd

from alerting import apply_acknowledgements, load_acknowledgements, notify, unused_acknowledgements
from detect import METRICS, THRESHOLD, detect, format_message

ROOT = Path(__file__).resolve().parents[1]


def load_metrics() -> pd.DataFrame:
    """Lit les indicateurs quotidiens (un jour x un opérateur par ligne)."""
    sys.path.append(str(ROOT / "ingestion"))
    from config import PROJECT_ID, check_project_id
    from google.cloud import bigquery

    check_project_id()
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        select pickup_date, license_num, day_of_week, is_expected_disruption, disruption_reason,
               nb_trips, share_flagged, share_timeline_anomaly, share_cbd_fee,
               avg_clean_driver_pay_usd, platform_margin_rate
        from `{PROJECT_ID}.dbt_dev_monitoring.dq_daily_metrics`
        order by pickup_date, license_num
    """
    df = client.query(sql).to_dataframe()
    df["pickup_date"] = pd.to_datetime(df["pickup_date"]).dt.date
    df["is_expected_disruption"] = df["is_expected_disruption"].astype(bool)
    df[list(METRICS)] = df[list(METRICS)].astype(float)   # nb_trips arrive en entier : on travaille en décimaux
    return df


def md_table(frame: pd.DataFrame, with_reason: bool) -> list:
    last = "raison de l'acquittement" if with_reason else "événement"
    out = [f"| jour | opérateur | indicateur | valeur | normale | score | {last} |", "|---|---|---|---|---|---|---|"]
    for _, r in frame.iterrows():
        extra = r["ack_reason"] if with_reason else (r["disruption_reason"] or "")
        out.append(f"| {r['pickup_date']} | {r['license_num']} | {r['label']} | {r['value']:.4g} | "
                   f"{r['normal']:.4g} | {r['z']:+.1f} | {extra} |")
    return out


def write_report(df: pd.DataFrame, alerts: pd.DataFrame, stale: pd.DataFrame) -> None:
    def part(name):
        return alerts[alerts["severity"] == name] if not alerts.empty else alerts

    open_, acked, info = part("alerte"), part("acquittée"), part("information")
    lines = ["# Rapport de santé des données", "",
             f"{df['pickup_date'].nunique()} jours, {df['license_num'].nunique()} opérateurs, {len(METRICS)} indicateurs surveillés, "
             f"seuil du score robuste : {THRESHOLD}.", "",
             f"- Alertes ouvertes : **{len(open_)}**",
             f"- Alertes acquittées après examen : **{len(acked)}**",
             f"- Informations (événements attendus) : **{len(info)}**", "",
             "## Alertes ouvertes", ""] + (md_table(open_, False) if len(open_) else ["Aucune."])
    lines += ["", "## Alertes acquittées", ""] + (md_table(acked, True) if len(acked) else ["Aucune."])
    lines += ["", "## Informations (événements attendus)", ""] + (md_table(info, False) if len(info) else ["Aucune."])
    if len(stale):
        lines += ["", "## Journal des acquittements à nettoyer", "",
                  "Ces lignes ne correspondent plus à aucune anomalie détectée :", ""]
        lines += [f"- {r['pickup_date']} {r['license_num']} {r['metric']}" for _, r in stale.iterrows()]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "data_health_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    df = load_metrics()
    alerts = detect(df)
    ack = load_acknowledgements()
    stale = unused_acknowledgements(alerts, ack)
    alerts = apply_acknowledgements(alerts, ack)
    print(f"{df['pickup_date'].nunique()} jours, {df['license_num'].nunique()} opérateurs, {len(ack)} acquittement(s) au journal")
    if not alerts.empty:
        show = alerts[["pickup_date", "license_num", "label", "value", "normal", "z", "severity", "disruption_reason"]].copy()
        show["value"] = show["value"].map(lambda v: f"{v:.4g}")
        show["normal"] = show["normal"].map(lambda v: f"{v:.4g}")
        show["z"] = show["z"].round(1)
        print(show.to_string(index=False))
    if len(stale):
        print(f"\nAttention : {len(stale)} ligne(s) du journal ne correspond(ent) à aucune anomalie.")

    write_report(df, alerts, stale)
    message = format_message(alerts)
    n_open = 0 if alerts.empty else int((alerts["severity"] == "alerte").sum())
    print()
    if n_open > 0:
        status = notify(message)          # affiche le message et l'envoie au webhook s'il est configuré
        print(f"({status})")
    else:
        print(message)
    print("\nÉcrit : docs/data_health_report.md")
    return 1 if (n_open > 0 and "--fail" in sys.argv) else 0


if __name__ == "__main__":
    sys.exit(main())