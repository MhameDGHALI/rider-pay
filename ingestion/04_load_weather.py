"""Étape 2.2 : charge la météo horaire (Open-Meteo) dans BigQuery (raw.weather_hourly).

Si data/raw/archive-meteo.json n'existe pas, le script le télécharge depuis l'API.
Les heures sont en heure locale de New York, comme les courses TLC.
"""
import json

import pandas as pd

from config import DATA_RAW, LOCATION, PROJECT_ID, RAW_DATASET, check_project_id

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=40.7128&longitude=-74.0060"
    "&start_date=2026-01-01&end_date=2026-02-28"
    "&hourly=temperature_2m,precipitation,rain,snowfall,wind_speed_10m"
    "&timezone=America/New_York"
)
JSON_PATH = DATA_RAW / "archive-meteo.json"


def fetch_if_missing():
    if JSON_PATH.exists():
        return
    import requests
    print("Téléchargement de la météo depuis Open-Meteo ...")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(resp.text, encoding="utf-8")


def build_dataframe() -> pd.DataFrame:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(data["hourly"])          # time, temperature_2m (°C), precipitation (mm),
    df["time"] = pd.to_datetime(df["time"])    # rain (mm), snowfall (cm), wind_speed_10m (km/h)
    return df


def main():
    check_project_id()
    from google.cloud import bigquery

    fetch_if_missing()
    df = build_dataframe()
    print(f"{len(df)} heures, de {df['time'].min()} à {df['time'].max()}")

    client = bigquery.Client(project=PROJECT_ID)
    dataset = bigquery.Dataset(f"{PROJECT_ID}.{RAW_DATASET}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)

    table_id = f"{PROJECT_ID}.{RAW_DATASET}.weather_hourly"
    job = client.load_table_from_dataframe(
        df, table_id,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    table = client.get_table(table_id)
    print(f"Table {table_id} : {table.num_rows} lignes")
    print("types :", {f.name: f.field_type for f in table.schema})


if __name__ == "__main__":
    main()