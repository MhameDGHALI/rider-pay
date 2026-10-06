"""Étape 2.1 : charge les échantillons de courses dans BigQuery (raw.hvfhv_trips).

- crée le dataset `raw` s'il n'existe pas ;
- table clusterisée par opérateur et zone de départ (PAS partitionnée : voir note) ;
- relançable sans risque : le premier fichier remplace la table, les suivants s'ajoutent.

Note : dans le sandbox BigQuery, toute partition expire 60 jours après sa date.
Nos courses datent de janvier-février 2026 : une table partitionnée par pickup_datetime
risquerait de voir ses partitions supprimées. On évite donc le partitionnement par date ici.
"""
from google.cloud import bigquery

from config import DATA_PROCESSED, LOCATION, PROJECT_ID, RAW_DATASET, check_project_id


def main():
    check_project_id()
    client = bigquery.Client(project=PROJECT_ID)

    dataset = bigquery.Dataset(f"{PROJECT_ID}.{RAW_DATASET}")
    dataset.location = LOCATION
    client.create_dataset(dataset, exists_ok=True)

    table_id = f"{PROJECT_ID}.{RAW_DATASET}.hvfhv_trips"
    files = sorted(DATA_PROCESSED.glob("hvfhv_sample_*.parquet"))
    if not files:
        raise SystemExit("Aucun échantillon trouvé : lance d'abord 01_sample_hvfhv.py")

    for i, path in enumerate(files):
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=(bigquery.WriteDisposition.WRITE_TRUNCATE if i == 0
                               else bigquery.WriteDisposition.WRITE_APPEND),
            clustering_fields=["hvfhs_license_num", "PULocationID"],
        )
        print(f"Chargement de {path.name} ...")
        with open(path, "rb") as fh:
            job = client.load_table_from_file(fh, table_id, job_config=job_config)
        job.result()  # attend la fin du chargement
        print("  OK")

    table = client.get_table(table_id)
    print(f"\nTable {table_id}")
    print(f"  lignes     : {table.num_rows:,}")
    print(f"  taille     : {table.num_bytes / 1e9:.2f} Go")
    print(f"  clustering : {table.clustering_fields}")
    print(f"  expiration : {table.expires}")
    print("  types des colonnes de date :")
    for f in table.schema:
        if f.name.endswith("_datetime"):
            print(f"    {f.name}: {f.field_type}")


if __name__ == "__main__":
    main()