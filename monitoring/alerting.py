"""Cycle de vie des alertes : acquittement après examen, et envoi du message.

- Une alerte examinée par une personne est ACQUITTÉE : elle reste visible dans le rapport avec sa raison,
  mais ne déclenche plus d'échec ni de notification. Le journal des acquittements est le fichier
  monitoring/acknowledged_alerts.csv (colonnes : pickup_date, license_num, metric, reason).
- L'envoi du message : affichage, et envoi à un webhook si la variable d'environnement ALERT_WEBHOOK_URL est définie
  (Slack, Teams ou équivalent : le message est envoyé dans le champ "text"). Aucun secret n'est écrit dans le dépôt.
"""
import json
import os
from pathlib import Path

import pandas as pd

ACK_PATH = Path(__file__).resolve().parent / "acknowledged_alerts.csv"
REQUIRED_COLUMNS = ["pickup_date", "license_num", "metric", "reason"]


def load_acknowledgements(path: Path = ACK_PATH) -> pd.DataFrame:
    """Lit le journal des alertes acquittées (vide si le fichier n'existe pas)."""
    if not Path(path).exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    ack = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in ack.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path} : {missing}")
    ack["pickup_date"] = pd.to_datetime(ack["pickup_date"]).dt.date
    return ack[REQUIRED_COLUMNS]


def apply_acknowledgements(alerts: pd.DataFrame, ack: pd.DataFrame) -> pd.DataFrame:
    """Passe en "acquittée" les alertes présentes dans le journal et ajoute leur raison."""
    out = alerts.copy()
    out["ack_reason"] = ""
    if out.empty or ack.empty:
        return out
    key = ["pickup_date", "license_num", "metric"]
    merged = out.merge(ack.rename(columns={"reason": "_reason"}), on=key, how="left")
    is_ack = (merged["severity"] == "alerte") & merged["_reason"].notna()
    merged.loc[is_ack, "severity"] = "acquittée"
    merged.loc[is_ack, "ack_reason"] = merged.loc[is_ack, "_reason"]
    return merged.drop(columns=["_reason"])


def unused_acknowledgements(alerts: pd.DataFrame, ack: pd.DataFrame) -> pd.DataFrame:
    """Lignes du journal qui ne correspondent à aucune anomalie détectée (journal périmé, ou faute de frappe)."""
    if ack.empty:
        return ack
    key = ["pickup_date", "license_num", "metric"]
    if alerts.empty:
        return ack
    merged = ack.merge(alerts[key].drop_duplicates().assign(_seen=True), on=key, how="left")
    return merged[merged["_seen"].isna()][REQUIRED_COLUMNS]


def notify(message: str, webhook_url: str = None) -> str:
    """Affiche le message et l'envoie au webhook s'il y en a un. Retourne l'état de l'envoi."""
    print(message)
    url = webhook_url if webhook_url is not None else os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        return "aucun webhook configuré : message affiché seulement"
    import requests

    response = requests.post(url, data=json.dumps({"text": message}),
                             headers={"Content-Type": "application/json"}, timeout=15)
    response.raise_for_status()
    return f"message envoyé (code {response.status_code})"