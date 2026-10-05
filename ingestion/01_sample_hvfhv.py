"""Étape 1.1 : échantillonne les fichiers HVFHS (30 %, seed 42) et ne garde que les colonnes utiles.

Entrée  : data/raw/fhvhv_tripdata_YYYY-MM.parquet
Sortie  : data/processed/hvfhv_sample_YYYY-MM.parquet

Le fichier est lu par morceaux (500 000 lignes à la fois) pour ne pas saturer la mémoire.
Chaque course reçoit un trip_id = "<mois>-<numéro de ligne dans le fichier d'origine>",
car les données TLC n'ont pas d'identifiant de course.
"""
import re

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from config import DATA_PROCESSED, DATA_RAW, KEEP_COLUMNS, SAMPLE_FRACTION, SEED


def sample_file(src, dst, month, fraction=SAMPLE_FRACTION, seed=SEED, batch_size=500_000):
    pf = pq.ParquetFile(src)
    total = pf.metadata.num_rows
    rng = np.random.default_rng(seed)  # générateur aléatoire reproductible
    writer = None
    offset = 0   # numéro de la première ligne du morceau dans le fichier d'origine
    kept = 0

    for batch in pf.iter_batches(batch_size=batch_size, columns=KEEP_COLUMNS):
        n = batch.num_rows
        keep_idx = np.nonzero(rng.random(n) < fraction)[0]   # ~30 % des positions

        sub = batch.take(pa.array(keep_idx))
        trip_ids = pa.array([f"{month}-{offset + int(i)}" for i in keep_idx], type=pa.string())
        sub = sub.append_column("trip_id", trip_ids)
        table = pa.Table.from_batches([sub])

        if writer is None:
            writer = pq.ParquetWriter(dst, table.schema, compression="snappy")
        writer.write_table(table)

        offset += n
        kept += len(keep_idx)
        print(f"  {offset:>12,} / {total:,} lignes lues, {kept:,} gardées", end="\r")

    if writer is not None:
        writer.close()
    print()
    return total, kept


def main():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_RAW.glob("fhvhv_tripdata_*.parquet"))
    if not files:
        raise SystemExit(f"Aucun fichier fhvhv_tripdata_*.parquet trouvé dans {DATA_RAW}")

    for src in files:
        month = re.search(r"(\d{4}-\d{2})", src.name).group(1)
        dst = DATA_PROCESSED / f"hvfhv_sample_{month}.parquet"
        print(f"[{month}] {src.name} -> {dst.name}")
        total, kept = sample_file(src, dst, month)
        size_mb = dst.stat().st_size / 1_048_576
        print(f"[{month}] terminé : {kept:,} lignes sur {total:,} ({kept / total:.1%}), {size_mb:.0f} Mo\n")


if __name__ == "__main__":
    main()