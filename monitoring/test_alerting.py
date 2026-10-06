"""Tests du cycle de vie des alertes (acquittement et envoi). Aucun accès à BigQuery ni à Internet.

Lancer depuis la racine du projet : python monitoring/test_alerting.py
"""
import datetime as dt

import numpy as np
import pandas as pd

from alerting import apply_acknowledgements, notify, unused_acknowledgements
from detect import detect, format_message
from test_detect import inject, make_series


def main() -> None:
    rng = np.random.default_rng(3)
    df = make_series(rng)
    df = inject(df, dt.date(2026, 1, 22), "HV0005", "share_flagged", add=0.09)
    df = inject(df, dt.date(2026, 2, 12), "HV0003", "avg_clean_driver_pay_usd", factor=1.3)
    alerts = detect(df)
    assert (alerts["severity"] == "alerte").sum() == 2, "deux alertes ouvertes attendues"

    # 1. Acquitter une alerte la sort des alertes ouvertes, mais elle reste visible avec sa raison
    ack = pd.DataFrame([{"pickup_date": dt.date(2026, 1, 22), "license_num": "HV0005",
                         "metric": "share_flagged", "reason": "incident connu"}])
    after = apply_acknowledgements(alerts, ack)
    assert (after["severity"] == "alerte").sum() == 1
    assert (after["severity"] == "acquittée").sum() == 1
    assert after.loc[after["severity"] == "acquittée", "ack_reason"].iloc[0] == "incident connu"
    print("  OK  une alerte acquittée n'est plus ouverte et garde sa raison")

    # 2. Le message ne mentionne que les alertes ouvertes
    message = format_message(after)
    assert "1 alerte(s)" in message and "2026-02-12" in message and "2026-01-22" not in message
    print("  OK  le message ne liste que les alertes ouvertes")

    # 3. Une ligne du journal qui ne correspond plus à rien est repérée
    stale = pd.concat([ack, pd.DataFrame([{"pickup_date": dt.date(2026, 1, 5), "license_num": "HV0003",
                                           "metric": "nb_trips", "reason": "ancienne alerte"}])])
    leftover = unused_acknowledgements(alerts, stale)
    assert len(leftover) == 1 and leftover.iloc[0]["pickup_date"] == dt.date(2026, 1, 5)
    print("  OK  une ligne périmée du journal est repérée")

    # 4. Sans webhook, le message est seulement affiché
    status = notify("test", webhook_url="")
    assert "aucun webhook" in status
    print("  OK  sans webhook, pas d'envoi")
    print("OK")


if __name__ == "__main__":
    main()