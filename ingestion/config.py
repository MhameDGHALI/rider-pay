"""Configuration commune à tous les scripts d'ingestion.

Seule valeur à modifier : PROJECT_ID (ou définir la variable d'environnement GCP_PROJECT_ID).
"""
import os
from pathlib import Path

# --- Google Cloud -----------------------------------------------------------
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")  # <-- à remplacer au jour 2
LOCATION = "US"          # région du dataset BigQuery (doit rester la même partout)
RAW_DATASET = "raw"      # dataset qui contient les données brutes

# --- Chemins ----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"              # fichiers téléchargés (non versionnés)
DATA_PROCESSED = ROOT / "data" / "processed"  # échantillons générés (non versionnés)
DATA_REFERENCE = ROOT / "data" / "reference"  # petits fichiers de référence
DOCS = ROOT / "docs"

# --- Échantillonnage --------------------------------------------------------
SAMPLE_FRACTION = 0.30   # on garde ~30 % des courses
SEED = 42                # graine fixe : résultat reproductible

# --- Colonnes TLC conservées (on retire dispatching_base_num et access_a_ride_flag)
KEEP_COLUMNS = [
    "hvfhs_license_num", "originating_base_num",
    "request_datetime", "on_scene_datetime", "pickup_datetime", "dropoff_datetime",
    "PULocationID", "DOLocationID",
    "trip_miles", "trip_time",
    "base_passenger_fare", "tolls", "bcf", "sales_tax",
    "congestion_surcharge", "airport_fee", "cbd_congestion_fee",
    "tips", "driver_pay",
    "shared_request_flag", "shared_match_flag", "wav_request_flag", "wav_match_flag",
]


def check_project_id() -> None:
    """Arrête le script si le PROJECT_ID n'a pas été renseigné."""
    if PROJECT_ID == "YOUR_PROJECT_ID":
        raise SystemExit(
            "Renseigne ton Project ID dans ingestion/config.py "
            "(ou définis la variable d'environnement GCP_PROJECT_ID)."
        )