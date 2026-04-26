"""
admin_extract_epci_data.py — Extraction EPCI par BBOX via DuckDB (Instructeur)
==============================================================================
Filtre les fichiers Parquet nationaux (poi_source/) par EPCI BBOX et écrit
des petits parquets dans data/epci_extracts/{siren}/.

Usage :
    python scripts/admin_extract_epci_data.py --epci 242900314
    python scripts/admin_extract_epci_data.py --all
"""

import argparse
import os
import time

import duckdb
import pandas as pd
from shapely import wkb

# =============================================================================
# CONFIG
# =============================================================================

EPCI_PARQUET = "data/epci.parquet"
SOURCE_DIR = "data/poi_source"
OUTPUT_DIR = "data/epci_extracts"

SELECTED_EPCIS = [
    "242900314",  # Brest Métropole
    "200084952",  # Le Havre Seine Métropole
    "245900428",  # CU de Dunkerque
    "200067205",  # CA du Cotentin
    "200040715",  # Grenoble-Alpes-Métropole
    "246700488",  # Eurométropole de Strasbourg
    "200093201",  # Métropole Européenne de Lille
    "200067106",  # CA du Pays Basque
    "200023414",  # Métropole Rouen Normandie
    "243300316",  # Bordeaux Métropole
    "244400404",  # Nantes Métropole
    "200046977",  # Métropole de Lyon
    "243700754",  # Tours Métropole Val de Loire
]

con = duckdb.connect()


def get_epci_bbox(df_epci, siren):
    res = df_epci[df_epci["code_siren"] == siren]
    if res.empty:
        raise ValueError(f"EPCI '{siren}' non trouvé.")
    row = res.iloc[0]
    bb = row["geometrie_bbox"]
    return row["nom_officiel"], siren, bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"]


def extract_table(table_name, bbox, out_path):
    src = f"{SOURCE_DIR}/{table_name}.parquet"
    if not os.path.exists(src):
        return 0

    xmin, ymin, xmax, ymax = bbox
    # DuckDB : filtre BBOX via les colonnes geometrie_bbox struct
    # Pour les tables sans geometrie_bbox, copie intégrale
    try:
        con.execute(f"""
            COPY (
                SELECT * FROM read_parquet('{src}')
                WHERE geometrie_bbox.xmin < {xmax}
                  AND geometrie_bbox.xmax > {xmin}
                  AND geometrie_bbox.ymin < {ymax}
                  AND geometrie_bbox.ymax > {ymin}
            ) TO '{out_path}' (FORMAT PARQUET)
        """)
        return con.execute(f"SELECT count(*) FROM read_parquet('{out_path}')").fetchone()[0]
    except duckdb.CatalogException:
        # Pas de colonne geometrie_bbox → copie intégrale
        con.execute(f"COPY (SELECT * FROM read_parquet('{src}')) TO '{out_path}' (FORMAT PARQUET)")
        return con.execute(f"SELECT count(*) FROM read_parquet('{out_path}')").fetchone()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--epci", help="code_siren d'un EPCI (9 chiffres)")
    args = parser.parse_args()

    targets = SELECTED_EPCIS if args.all else ([args.epci] if args.epci else [])
    if not targets:
        parser.error("--all ou --epci requis")
        return

    df_epci = pd.read_parquet(EPCI_PARQUET)
    source_tables = sorted(f.replace(".parquet", "") for f in os.listdir(SOURCE_DIR)
                           if f.endswith(".parquet"))

    for siren in targets:
        name, _, xmin, ymin, xmax, ymax = get_epci_bbox(df_epci, siren)
        print(f"\n{'='*60}\n  {name} ({siren})\n  BBOX: [{xmin:.3f}, {ymin:.3f}, {xmax:.3f}, {ymax:.3f}]\n{'='*60}")

        epci_dir = f"{OUTPUT_DIR}/{siren}"
        os.makedirs(epci_dir, exist_ok=True)
        total_rows = 0

        for tbl in source_tables:
            out = f"{epci_dir}/{tbl}.parquet"
            t0 = time.time()
            rows = extract_table(tbl, (xmin, ymin, xmax, ymax), out)
            dt = time.time() - t0
            total_rows += rows
            if rows > 0:
                print(f"  [OK] {tbl:<35} {rows:>8} rows  ({dt:.1f}s)")

        print(f"\n  Total: {total_rows:,} rows → {epci_dir}/")


if __name__ == "__main__":
    main()
