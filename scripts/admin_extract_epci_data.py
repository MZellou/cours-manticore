"""
admin_extract_epci_data.py — Extraction EPCI depuis sources nationales (Instructeur)
==================================================================================
Filtre les fichiers Parquet nationaux (poi_source/) par EPCI et écrit
des petits parquets dans data/epci_extracts/{siren}/.

Usage :
    python scripts/admin_extract_epci_data.py --epci "Brest Métropole"
    python scripts/admin_extract_epci_data.py --all
"""

import argparse
import os
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import prepared, wkb

# =============================================================================
# CONFIG
# =============================================================================

EPCI_PARQUET = "data/epci.parquet"
SOURCE_DIR = "data/poi_source"
OUTPUT_DIR = "data/epci_extracts"

SELECTED_EPCIS = [
    "Brest Métropole",
    "Le Havre Seine Métropole",
    "CU de Dunkerque",
    "CA du Cotentin",
    "Grenoble-Alpes-Métropole",
    "Eurométropole de Strasbourg",
    "Métropole Européenne de Lille",
    "CA du Pays Basque",
    "Métropole Rouen Normandie",
    "Bordeaux Métropole",
]


def get_epci_info(df_epci, query):
    mask = (df_epci["code_siren"] == query) | (
        df_epci["nom_officiel"].str.contains(query, case=False, na=False)
    )
    res = df_epci[mask]
    if res.empty:
        raise ValueError(f"EPCI '{query}' non trouvé.")
    if len(res) > 1:
        print(f"  [WARN] Plusieurs EPCIs pour '{query}', on prend le premier.")
    row = res.iloc[0]
    geom = wkb.loads(row["geometrie"])
    bb = row["geometrie_bbox"]
    return row["nom_officiel"], row["code_siren"], geom, prepared.prep(geom), (
        bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"]
    )


def find_bbox_col_idx(rg_meta):
    """Trouve l'index de colonne pour geometrie_bbox.xmax dans les stats."""
    for i in range(rg_meta.num_columns):
        if rg_meta.column(i).path_in_schema == "geometrie_bbox.xmax":
            return i
    return -1


def extract_table(table_name, source_path, bbox, prep_geom, out_path):
    if not os.path.exists(source_path):
        return 0, 0

    pf = pq.ParquetFile(source_path)
    has_geom = "geometrie" in pf.schema_arrow.names

    # BBOX pushdown via stats Parquet (xmin/xmax/ymin/ymax par row group)
    kept_rgs = []
    for rg_idx in range(pf.metadata.num_row_groups):
        if not has_geom:
            kept_rgs.append(rg_idx)
            continue
        rg = pf.metadata.row_group(rg_idx)
        bbox_idx = find_bbox_col_idx(rg)
        if bbox_idx < 0:
            kept_rgs.append(rg_idx)
            continue
        # xmin stat = bbox_idx - 3, ymin = -2, xmax = -1 (this one), ymax = +1
        xmin_s = rg.column(bbox_idx - 3).statistics
        xmax_s = rg.column(bbox_idx).statistics
        ymin_s = rg.column(bbox_idx - 2).statistics
        ymax_s = rg.column(bbox_idx + 1).statistics
        if not all(s and s.has_min_max for s in [xmin_s, xmax_s, ymin_s, ymax_s]):
            kept_rgs.append(rg_idx)
            continue
        if (float(xmin_s.max) < bbox[2] and float(xmax_s.min) > bbox[0]
                and float(ymin_s.max) < bbox[3] and float(ymax_s.min) > bbox[1]):
            kept_rgs.append(rg_idx)

    if not kept_rgs:
        return 0, pf.metadata.num_rows

    # Lire + filtrer par shapely intersection
    tables = []
    for rg_idx in kept_rgs:
        t = pf.read_row_group(rg_idx)
        if has_geom:
            df = t.to_pandas()
            df["_shape"] = df["geometrie"].apply(lambda x: wkb.loads(x) if x else None)
            df = df[df["_shape"].apply(lambda x: prep_geom.intersects(x) if x else False)]
            df = df.drop(columns=["_shape"])
            if not df.empty:
                tables.append(pa.Table.from_pandas(df))
        else:
            tables.append(t)

    if not tables:
        return 0, pf.metadata.num_rows

    result = pa.concat_tables(tables)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pq.write_table(result, out_path)
    return result.num_rows, pf.metadata.num_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--epci", help="Nom ou SIREN d'un EPCI")
    args = parser.parse_args()

    targets = SELECTED_EPCIS if args.all else ([args.epci] if args.epci else [])
    if not targets:
        parser.error("--all ou --epci requis")
        return

    df_epci = pd.read_parquet(EPCI_PARQUET)
    source_tables = sorted(f.replace(".parquet", "") for f in os.listdir(SOURCE_DIR)
                           if f.endswith(".parquet"))

    for query in targets:
        name, siren, geom, prep_geom, bbox = get_epci_info(df_epci, query)
        print(f"\n{'='*60}\n  {name} ({siren})\n{'='*60}")

        total_rows = 0
        for tbl in source_tables:
            src = f"{SOURCE_DIR}/{tbl}.parquet"
            out = f"{OUTPUT_DIR}/{siren}/{tbl}.parquet"
            t0 = time.time()
            rows, total = extract_table(tbl, src, bbox, prep_geom, out)
            dt = time.time() - t0
            total_rows += rows
            if rows > 0:
                print(f"  [OK] {tbl:<35} {rows:>8} rows  ({dt:.1f}s)")
            elif total > 0:
                print(f"  [--] {tbl:<35} 0 rows (filtered out)")

        print(f"\n  Total: {total_rows:,} rows → {OUTPUT_DIR}/{siren}/")


if __name__ == "__main__":
    main()
