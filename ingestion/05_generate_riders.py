"""Étape 2.3 : génère la table SYNTHÉTIQUE des riders (raw.riders_synthetic).

Les données TLC n'ont pas d'identifiant de chauffeur. On fabrique donc un parc de riders,
reproductible (seed fixe). Hypothèses (à citer dans le README) :
  - 5 000 riders ; 75 % Uber (HV0003) / 25 % Lyft (HV0005), hypothèse de départ ;
  - niveaux bronze 60 % / silver 30 % / gold 10 % ;
  - ancienneté de 1 à 60 mois.
L'affectation des courses aux riders se fera plus tard, en SQL (dbt), à partir du trip_id.
"""
import numpy as np
import pandas as pd

from config import DATA_PROCESSED, LOCATION, PROJECT_ID, RAW_DATASET, SEED, check_project_id

N_RIDERS = 5_000
REFERENCE_DATE = pd.Timestamp("2026-01-01")


def build_dataframe() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    tenure = rng.integers(1, 61, size=N_RIDERS)
    df = pd.DataFrame({
        "rider_id": np.arange(1, N_RIDERS + 1),
        "hvfhs_license_num": rng.choice(["HV0003", "HV0005"], size=N_RIDERS, p=[0.75, 0.25]),
        "tier": rng.choice(["bronze", "silver", "gold"], size=N_RIDERS, p=[0.60, 0.30, 0.10]),
        "tenure_months": tenure,
    })
    df["signup_date"] = [(REFERENCE_DATE - pd.DateOffset(months=int(m))).date() for m in tenure]
    return df


def main():
    check_project_id()
    from google.cloud import bigquery

    df = build_dataframe()
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PROCESSED / "riders_synthetic.csv", index=False)

    client = bigquery.Client(project=PROJECT_ID)
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{RAW_DATASET}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)

    table_id = f"{PROJECT_ID}.{RAW_DATASET}.riders_synthetic"
    job = client.load_table_from_dataframe(
        df, table_id,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    print(f"Table {table_id} : {client.get_table(table_id).num_rows} lignes")
    print(df["tier"].value_counts(normalize=True).round(3).to_dict())


if __name__ == "__main__":
    main()