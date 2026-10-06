"""Contrôle de santé des données : lit les indicateurs quotidiens dans BigQuery, détecte les anomalies,
affiche les alertes et écrit un rapport.

Lancer depuis la racine du projet :  python monitoring/run_checks.py
Option : --fail  quitte avec un code d'erreur s'il y a au moins une alerte (utile pour une exécution automatique).

Entrée : BigQuery, table dbt_dev_monitoring.dq_daily_metrics
Sortie : docs/data_health_report.md
"""
import sys
from pathlib import Path

import pandas as pd

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
    return df


def write_report(df: pd.DataFrame, alerts: pd.DataFrame) -> None:
    real = alerts[alerts["severity"] == "alerte"] if not alerts.empty else alerts
    info = alerts[alerts["severity"] == "information"] if not alerts.empty else alerts
    lines = ["# Rapport de santé des données", "",
             f"{df['pickup_date'].nunique()} jours, {df['license_num'].nunique()} opérateurs, {len(METRICS)} indicateurs surveillés, "
             f"seuil du score robuste : {THRESHOLD}.", "",
             f"- Alertes (anomalies sans événement attendu) : **{len(real)}**",
             f"- Informations (anomalies expliquées par un événement attendu) : **{len(info)}**", ""]

    def table(frame: pd.DataFrame) -> list:
        out = ["| jour | opérateur | indicateur | valeur | normale | score | événement |", "|---|---|---|---|---|---|---|"]
        for _, r in frame.iterrows():
            out.append(f"| {r['pickup_date']} | {r['license_num']} | {r['label']} | {r['value']:.4g} | "
                       f"{r['normal']:.4g} | {r['z']:+.1f} | {r['disruption_reason'] or ''} |")
        return out

    lines += ["## Alertes", ""] + (table(real) if len(real) else ["Aucune."])
    lines += ["", "## Informations (événements attendus)", ""] + (table(info) if len(info) else ["Aucune."])
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "data_health_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    df = load_metrics()
    alerts = detect(df)
    print(f"{df['pickup_date'].nunique()} jours, {df['license_num'].nunique()} opérateurs")
    if not alerts.empty:
        show = alerts[["pickup_date", "license_num", "label", "value", "normal", "z", "severity", "disruption_reason"]].copy()
        show["value"] = show["value"].map(lambda v: f"{v:.4g}")
        show["normal"] = show["normal"].map(lambda v: f"{v:.4g}")
        show["z"] = show["z"].round(1)
        print(show.to_string(index=False))
    print("\n" + format_message(alerts))
    write_report(df, alerts)
    print("\nÉcrit : docs/data_health_report.md")
    n_alerts = 0 if alerts.empty else int((alerts["severity"] == "alerte").sum())
    return 1 if (n_alerts > 0 and "--fail" in sys.argv) else 0


if __name__ == "__main__":
    sys.exit(main())