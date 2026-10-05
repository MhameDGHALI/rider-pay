"""Étape 1.2 : vérifie que l'échantillon ressemble au fichier complet.

Compare, pour chaque mois : nombre de lignes, part Uber, rémunération moyenne,
distance moyenne, part plateforme et répartition par borough.
Écrit le résultat dans docs/sampling_check.md (à citer dans le README).
"""
import re

import pandas as pd
import pyarrow.parquet as pq

from config import DATA_PROCESSED, DATA_RAW, DATA_REFERENCE, DOCS

COLS = ["hvfhs_license_num", "driver_pay", "trip_miles", "base_passenger_fare", "PULocationID"]


def load(path, zones):
    df = pq.read_table(path, columns=COLS).to_pandas(strings_to_categorical=True)
    return df.merge(zones[["LocationID", "Borough"]], left_on="PULocationID",
                    right_on="LocationID", how="left")


def metrics(df):
    return {
        "lignes": len(df),
        "part Uber (HV0003)": (df["hvfhs_license_num"] == "HV0003").mean(),
        "driver_pay moyen ($)": df["driver_pay"].mean(),
        "trip_miles moyen": df["trip_miles"].mean(),
        # part gardée par la plateforme (approximation sur le tarif de base)
        "part plateforme": 1 - df["driver_pay"].sum() / df["base_passenger_fare"].sum(),
    }


def main():
    zones = pd.read_csv(DATA_REFERENCE / "taxi_zone_lookup.csv")
    lines = ["# Contrôle de représentativité de l'échantillon\n"]

    for sample_path in sorted(DATA_PROCESSED.glob("hvfhv_sample_*.parquet")):
        month = re.search(r"(\d{4}-\d{2})", sample_path.name).group(1)
        full_path = DATA_RAW / f"fhvhv_tripdata_{month}.parquet"
        if not full_path.exists():
            print(f"[{month}] fichier complet absent, ignoré")
            continue

        full, samp = load(full_path, zones), load(sample_path, zones)
        mf, ms = metrics(full), metrics(samp)

        table = pd.DataFrame({"complet": mf, "échantillon": ms})
        table["écart relatif"] = (table["échantillon"] / table["complet"] - 1)
        # le nombre de lignes doit valoir ~30 %, ce n'est pas un écart à lire
        table.loc["lignes", "écart relatif"] = float("nan")

        boro = pd.DataFrame({
            "complet": full["Borough"].value_counts(normalize=True),
            "échantillon": samp["Borough"].value_counts(normalize=True),
        })
        boro["écart (points)"] = (boro["échantillon"] - boro["complet"]) * 100

        block = (f"\n## {month}\n\n```\n{table.round(4).to_string()}\n```\n\n"
                 f"Répartition par borough de prise en charge :\n\n```\n{boro.round(4).to_string()}\n```\n")
        print(block)
        lines.append(block)

    DOCS.mkdir(exist_ok=True)
    (DOCS / "sampling_check.md").write_text("\n".join(lines), encoding="utf-8")
    print("Résultat écrit dans docs/sampling_check.md")


if __name__ == "__main__":
    main()