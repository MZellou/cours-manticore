"""
admin_generate_gold_dumps.py — Génération des graphes de routage pgRouting (Instructeur)
==========================================================================================

Pipeline par EPCI :
  1. LOAD  : Charge troncon_de_route + non_communication depuis les parquets EPCI → PostGIS
  2. PIVOT : r2gg-sql2pivot → transforme les tronçons en graphe nodes/edges
  3. PGR   : r2gg-pivot2pgrouting → convertit en tables pgRouting (ways + ways_vertices_pgr)
  4. DUMP  : Exporte les tables ways + ways_vertices_pgr en SQL dump

Usage :
    python scripts/admin_generate_gold_dumps.py --epci "Brest Métropole"
    python scripts/admin_generate_gold_dumps.py --all
    python scripts/admin_generate_gold_dumps.py --epci 242900314 --skip-load  # si tables déjà chargées

Prérequis :
    - Docker PostGIS avec pgRouting (docker compose up -d)
    - r2gg installé : pip install -e route-graph-generator/
    - Données EPCI dans data/epci_extracts/{siren}/
    - Fichiers r2gg SQL dans route-graph-generator/sql/
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

EPCI_PARQUET = "data/epci.parquet"
OUTPUT_DIR = "data/gold_dumps"
R2GG_DIR = "route-graph-generator"
EPCI_EXTRACTS_DIR = "data/epci_extracts"
R2GG_WORK_DIR = "data/gold_dumps/_r2gg_work"

# Tables nécessaires pour r2gg
R2GG_SOURCE_TABLES = ["troncon_de_route", "non_communication"]

# Les tables pgRouting générées
PGR_TABLES = ["ways", "ways_vertices_pgr", "turn_restrictions"]

SELECTED_EPCIS = {
    "242900314": "Brest Métropole",
    "200084952": "Le Havre Seine Métropole",
    "245900428": "CU de Dunkerque",
    "200067205": "CA du Cotentin",
    "200040715": "Grenoble-Alpes-Métropole",
    "246700488": "Eurométropole de Strasbourg",
    "200093201": "Métropole Européenne de Lille",
    "200067106": "CA du Pays Basque",
    "200023414": "Métropole Rouen Normandie",
    "243300316": "Bordeaux Métropole",
    "244400404": "Nantes Métropole",
    "200046977": "Métropole de Lyon",
    "243700754": "Tours Métropole Val de Loire",
}

# =============================================================================
# DB HELPERS
# =============================================================================

def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGIS_HOST", "localhost"),
        port=os.getenv("POSTGIS_PORT", "5432"),
        dbname=os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        user=os.getenv("POSTGIS_USER", "postgres"),
        password=os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    )

def get_psql_env():
    """Env dict for psql subprocess calls."""
    return {
        "PGHOST": os.getenv("POSTGIS_HOST", "localhost"),
        "PGPORT": os.getenv("POSTGIS_PORT", "5432"),
        "PGDATABASE": os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        "PGUSER": os.getenv("POSTGIS_USER", "postgres"),
        "PGPASSWORD": os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    }

# =============================================================================
# STEP 1 : LOAD — Charge les parquets EPCI dans PostGIS
# =============================================================================

def load_epci_tables(siren: str):
    """Charge troncon_de_route + non_communication depuis les parquets EPCI dans PostGIS.

    Utilise le script 00_setup.py avec --skip-spatial-filter si les données
    sont déjà extraites par EPCI. Mais pour r2gg, on a besoin de tables dans
    un schéma dédié (pas public) car r2gg utilise FDW.

    En pratique, on charge directement via DuckDB → PostGIS pour les 2 tables.
    """
    import pyarrow.parquet as pq

    conn = get_conn()
    conn.autocommit = True
    extract_dir = Path(EPCI_EXTRACTS_DIR) / siren

    for table_name in R2GG_SOURCE_TABLES:
        parquet_path = extract_dir / f"{table_name}.parquet"
        if not parquet_path.exists():
            print(f"    [SKIP] {table_name} — fichier absent: {parquet_path}")
            continue

        print(f"    Loading {table_name}...")
        t0 = time.time()

        # Drop + create avec géométrie en EPSG:2154 (native BDTOPO)
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            cur.execute("DROP EXTENSION IF EXISTS postgres_fdw CASCADE;")

        # Utiliser \copy via psql est plus rapide, mais on fait du Python simple
        # On charge le parquet en pandas puis insert par batch
        df = pd.read_parquet(parquet_path)
        if df.empty:
            print(f"    [SKIP] {table_name} — parquet vide")
            continue

        # Créer la table avec les bons types
        cols = []
        col_names = []
        for col_name in df.columns:
            col_names.append(col_name)
            dtype = df[col_name].dtype
            if col_name == "geometrie":
                continue  # géométrie ajoutée séparément
            elif col_name == "geometrie_bbox":
                continue  # pas besoin pour r2gg
            elif "int" in str(dtype):
                cols.append(f'"{col_name}" BIGINT')
            elif "float" in str(dtype) or "double" in str(dtype):
                cols.append(f'"{col_name}" DOUBLE PRECISION')
            elif "bool" in str(dtype):
                cols.append(f'"{col_name}" BOOLEAN')
            else:
                cols.append(f'"{col_name}" TEXT')

        has_geom = "geometrie" in df.columns

        # Trouver les colonnes qu'on va réellement insérer
        insert_cols = [c for c in col_names if c not in ("geometrie", "geometrie_bbox")]

        with conn.cursor() as cur:
            # geometry sans contrainte de type/dimension — accepte 2D et 3D
            geom_col = ', "geometrie" geometry' if has_geom else ''
            cur.execute(f"CREATE TABLE {table_name} ({', '.join(cols)}{geom_col});")

        # Insert par batch
        from psycopg2.extras import execute_values
        batch_size = 1000
        total = 0

        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            data = []
            for _, row in batch.iterrows():
                vals = []
                for c in insert_cols:
                    v = row[c]
                    if pd.isna(v):
                        vals.append(None)
                    elif isinstance(v, bytes):
                        vals.append(None)  # skip raw bytes
                    else:
                        vals.append(v)
                if has_geom and row.get("geometrie") is not None:
                    import psycopg2
                    vals.append(psycopg2.Binary(row["geometrie"]))
                data.append(tuple(vals))

            quoted = [f'"{c}"' for c in insert_cols]
            if has_geom:
                quoted.append('"geometrie"')
            sql = f"INSERT INTO {table_name} ({', '.join(quoted)}) VALUES %s"

            with conn.cursor() as cur:
                execute_values(cur, sql, data, page_size=500)
            total += len(batch)

        dt = time.time() - t0
        print(f"    [OK] {table_name}: {total} lignes en {dt:.1f}s")

    # Créer les index spatiaux
    print("    Creating spatial indexes...")
    with conn.cursor() as cur:
        for table_name in R2GG_SOURCE_TABLES:
            try:
                # Fix SRID: BDTOPO parquets are in EPSG:4326
                cur.execute(f"UPDATE {table_name} SET geometrie = ST_SetSRID(geometrie, 4326) WHERE ST_SRID(geometrie) = 0;")
                cur.execute(f"CREATE INDEX idx_{table_name}_geom ON {table_name} USING GIST (geometrie);")
            except Exception:
                pass  # table peut ne pas exister
    conn.close()

# =============================================================================
# STEP 2+3 : R2GG — Génère le graphe pgRouting via r2gg
# =============================================================================

def generate_r2gg_configs(siren: str, bbox: tuple) -> Path:
    """Génère les fichiers de config JSON pour r2gg (DB + main config + log + costs).

    Retourne le chemin vers le fichier de config principal.
    """
    epci_dir = Path(OUTPUT_DIR) / siren
    epci_dir.mkdir(parents=True, exist_ok=True)

    r2gg_config_dir = epci_dir / "r2gg_config"
    r2gg_config_dir.mkdir(exist_ok=True)

    # DB config — même base pour pivot et sortie
    db_config = {
        "host": os.getenv("POSTGIS_HOST", "localhost"),
        "port": os.getenv("POSTGIS_PORT", "5432"),
        "database": os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        "user": os.getenv("POSTGIS_USER", "postgres"),
        "password": os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    }

    # db_pivot.json — lit les tables source (troncon_de_route, non_communication)
    pivot_config = {**db_config, "schema": "public"}
    with open(r2gg_config_dir / "db_pivot.json", "w") as f:
        json.dump(pivot_config, f, indent=2)

    # db_output.json — écrit les tables pgRouting dans un schéma dédié
    output_schema = f"pgr_{siren}"
    output_config = {**db_config, "schema": output_schema}
    with open(r2gg_config_dir / "db_output.json", "w") as f:
        json.dump(output_config, f, indent=2)

    # Log config
    log_config = {
        "level": "INFO",
        "filename": str(r2gg_config_dir / "r2gg.log")
    }
    with open(r2gg_config_dir / "log_config.json", "w") as f:
        json.dump(log_config, f, indent=2)

    # Costs config (format r2gg)
    costs_config = {
        "variables": [
            {"name": "nature", "column_name": "nature", "mapping": "value"},
            {"name": "length_m", "column_name": "length_m", "mapping": "value"},
            {"name": "vitesse_voiture", "column_name": "vitesse_moyenne_vl", "mapping": "value"},
            {"name": "sens", "column_name": "direction", "mapping": "value"},
            {"name": "acces_pieton", "column_name": "acces_pieton", "mapping": "value"},
            {"name": "urbain", "column_name": "urbain", "mapping": {"True": 5, "False": 0}},
        ],
        "outputs": [
            {
                "name": "cost_m_car",
                "speed_value": "vitesse_voiture",
                "direct_conditions": "sens>=0;vitesse_voiture>0",
                "reverse_conditions": "sens<=0;vitesse_voiture>0",
                "turn_restrictions": True,
                "cost_type": "distance",
                "operations": [["add", "length_m"]],
            },
            {
                "name": "cost_s_car",
                "speed_value": "vitesse_voiture",
                "direct_conditions": "sens>=0;vitesse_voiture>0",
                "reverse_conditions": "sens<=0;vitesse_voiture>0",
                "turn_restrictions": True,
                "cost_type": "duration",
                "operations": [["add", "length_m"], ["divide", "vitesse_voiture"], ["multiply", 3.6], ["add", "urbain"]],
            },
        ],
    }
    with open(r2gg_config_dir / "costs.json", "w") as f:
        json.dump(costs_config, f, indent=2)

    # Work directory
    work_dir = Path(R2GG_WORK_DIR) / siren
    work_dir.mkdir(parents=True, exist_ok=True)

    # Main config r2gg
    main_config = {
        "generation": {
            "general": {
                "id": f"manticore_{siren}",
                "overwrite": True,
                "operation": "creation",
                "logs": {
                    "configFile": str(r2gg_config_dir / "log_config.json")
                }
            },
            "bases": [
                {
                    "id": "base_pivot",
                    "type": "bdd",
                    "configFile": str(r2gg_config_dir / "db_pivot.json"),
                    "schema": "public"
                },
                {
                    "id": "base_sortie",
                    "type": "bdd",
                    "configFile": str(r2gg_config_dir / "db_output.json"),
                    "schema": output_schema
                }
            ],
            "workingSpace": {
                "directory": str(work_dir),
                "baseId": "base_pivot"
            },
            "resource": {
                "id": f"pgr_{siren}",
                "type": "pgr",
                "sources": [
                    {
                        "id": "bdtopo",
                        "type": "pgr",
                        "projection": "EPSG:4326",
                        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                        "mapping": {
                            "source": {
                                "baseId": "base_pivot"
                            },
                            "conversion": {
                                "file": str(Path(R2GG_DIR) / "sql" / "bdtopo_v3.3_local.sql")
                            }
                        },
                        "storage": {
                            "base": {
                                "baseId": "base_sortie",
                                "attributes": [
                                    {"key": "cleabs", "column": "cleabs", "default": "false"},
                                    {"key": "nature", "column": "nature", "default": "false"},
                                    {"key": "importance", "column": "importance", "default": "false"},
                                    {"key": "sens_de_circulation", "column": "sens_de_circulation", "default": "false"},
                                    {"key": "vitesse_moyenne_vl", "column": "vitesse_moyenne_vl", "default": "false"},
                                    {"key": "position_par_rapport_au_sol", "column": "position_par_rapport_au_sol", "default": "false"},
                                    {"key": "nombre_de_voies", "column": "nombre_de_voies", "default": "false"},
                                    {"key": "largeur_de_chaussee", "column": "largeur_de_chaussee", "default": "false"},
                                    {"key": "matieres_dangereuses_interdites", "column": "matieres_dangereuses_interdites", "default": "false"},
                                    {"key": "restriction_de_hauteur", "column": "restriction_de_hauteur", "default": "false"},
                                    {"key": "restriction_de_poids_total", "column": "restriction_de_poids_total", "default": "false"},
                                    {"key": "restriction_de_largeur", "column": "restriction_de_largeur", "default": "false"},
                                    {"key": "restriction_de_longueur", "column": "restriction_de_longueur", "default": "false"},
                                ]
                            }
                        },
                        "costs": [
                            {
                                "profile": "car",
                                "optimization": "fastest",
                                "costType": "time",
                                "costColumn": "cost_s_car",
                                "rcostColumn": "reverse_cost_s_car",
                                "compute": {
                                    "storage": {"file": str(r2gg_config_dir / "costs.json")},
                                    "configuration": {
                                        "name": "cost_s_car",
                                        "storage": {"file": str(r2gg_config_dir / "costs.json")}
                                    }
                                }
                            },
                            {
                                "profile": "car",
                                "optimization": "shortest",
                                "costType": "distance",
                                "costColumn": "cost_m_car",
                                "rcostColumn": "reverse_cost_m_car",
                                "compute": {
                                    "storage": {"file": str(r2gg_config_dir / "costs.json")},
                                    "configuration": {
                                        "name": "cost_m_car",
                                        "storage": {"file": str(r2gg_config_dir / "costs.json")}
                                    }
                                }
                            },
                        ]
                    }
                ]
            }
        }
    }

    config_path = r2gg_config_dir / "r2gg_config.json"
    with open(config_path, "w") as f:
        json.dump(main_config, f, indent=2)

    return config_path


def run_r2gg(config_path: Path, step: str = "all"):
    """Lance r2gg (sql2pivot + pivot2pgrouting)."""
    import shlex

    # Vérifier que r2gg est installé
    r2gg_sql2pivot = shutil.which("r2gg-sql2pivot")
    r2gg_pivot2pgrouting = shutil.which("r2gg-pivot2pgrouting")

    if not r2gg_sql2pivot:
        print("  [INFO] r2gg CLI non trouvé dans PATH, utilisation de python -m")
        r2gg_sql2pivot = f"{sys.executable} -m r2gg.cli sql2pivot"
        r2gg_pivot2pgrouting = f"{sys.executable} -m r2gg.cli pivot2pgrouting"
    else:
        r2gg_sql2pivot = shlex.quote(r2gg_sql2pivot)
        r2gg_pivot2pgrouting = shlex.quote(r2gg_pivot2pgrouting)

    config_str = str(config_path)

    if step in ("pivot", "all"):
        print(f"  → r2gg-sql2pivot ...")
        t0 = time.time()
        result = subprocess.run(
            f"{r2gg_sql2pivot} {config_str}",
            shell=True, capture_output=True, text=True, timeout=600,
            env={**os.environ}
        )
        if result.returncode != 0:
            print(f"  ✗ r2gg-sql2pivot FAILED:")
            print(f"    STDOUT: {result.stdout[-2000:]}")
            print(f"    STDERR: {result.stderr[-2000:]}")
            raise RuntimeError(f"r2gg-sql2pivot failed (rc={result.returncode})")
        print(f"  ✓ r2gg-sql2pivot OK ({time.time() - t0:.1f}s)")

    if step in ("pgr", "all"):
        # Créer le schéma de sortie s'il n'existe pas
        config_data = json.loads(Path(config_str).read_text())
        out_schema = config_data["generation"]["resource"]["sources"][0]["storage"]["base"]["baseId"]
        # Trouver le schéma depuis les bases
        for base in config_data["generation"]["bases"]:
            if base["id"] == out_schema:
                schema_name = base["schema"]
                break
        else:
            schema_name = "public"

        conn = get_conn()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        conn.close()
        print(f"  → Schema {schema_name} prêt")

        print(f"  → r2gg-pivot2pgrouting ...")
        t0 = time.time()
        result = subprocess.run(
            f"{r2gg_pivot2pgrouting} {config_str}",
            shell=True, capture_output=True, text=True, timeout=600,
            env={**os.environ}
        )
        if result.returncode != 0:
            print(f"  ✗ r2gg-pivot2pgrouting FAILED:")
            print(f"    STDOUT: {result.stdout[-2000:]}")
            print(f"    STDERR: {result.stderr[-2000:]}")
            raise RuntimeError(f"r2gg-pivot2pgrouting failed (rc={result.returncode})")
        print(f"  ✓ r2gg-pivot2pgrouting OK ({time.time() - t0:.1f}s)")

# =============================================================================
# STEP 4 : DUMP — Exporte les tables pgRouting en SQL
# =============================================================================

def dump_routing_tables(siren: str):
    """Exporte les tables ways + ways_vertices_pgr en SQL dump."""
    epci_dir = Path(OUTPUT_DIR) / siren
    epci_dir.mkdir(parents=True, exist_ok=True)

    output_schema = f"pgr_{siren}"
    dump_path = epci_dir / "ways.sql"

    env = get_psql_env()

    print(f"  → Export pg_dump → {dump_path} ...")
    t0 = time.time()

    # pg_dump des tables du schéma pgr_{siren}
    cmd = [
        "pg_dump",
        "-h", env["PGHOST"],
        "-p", env["PGPORT"],
        "-U", env["PGUSER"],
        "-d", env["PGDATABASE"],
        "-n", output_schema,
        "--no-owner",
        "--no-privileges",
        "-f", str(dump_path),
    ]

    result = subprocess.run(
        cmd, env={**os.environ, **env}, capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    size_mb = dump_path.stat().st_size / 1024 / 1024
    print(f"  ✓ Dump OK: {dump_path} ({size_mb:.1f} MB, {time.time() - t0:.1f}s)")

# =============================================================================
# HELPERS
# =============================================================================

def get_epci_bbox(siren: str) -> tuple:
    """Récupère la BBOX d'un EPCI depuis le parquet."""
    df = pd.read_parquet(EPCI_PARQUET)
    res = df[df["code_siren"] == siren]
    if res.empty:
        raise ValueError(f"EPCI {siren} non trouvé dans {EPCI_PARQUET}")
    bb = res.iloc[0]["geometrie_bbox"]
    # r2gg attend du WGS84 (EPSG:4326) — vérifier si bbox est déjà en 4326
    # Les parquets EPCI stockent les bbox en 4326
    return (bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"])

def verify_r2gg_tables(siren: str):
    """Vérifie que les tables pgRouting ont bien été créées."""
    conn = get_conn()
    schema = f"pgr_{siren}"
    try:
        with conn.cursor() as cur:
            for table in PGR_TABLES:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name = %s)",
                    (schema, table)
                )
                exists = cur.fetchone()[0]
                if not exists:
                    print(f"  ⚠ Table {schema}.{table} n'existe pas")
                    return False

            # Compter les edges
            cur.execute(f"SELECT count(*) FROM {schema}.ways")
            n_ways = cur.fetchone()[0]
            cur.execute(f"SELECT count(*) FROM {schema}.ways_vertices_pgr")
            n_vertices = cur.fetchone()[0]
            print(f"  ✓ Vérifié: {n_ways} ways, {n_vertices} vertices dans {schema}")
            return True
    finally:
        conn.close()

# =============================================================================
# MAIN
# =============================================================================

def process_epci(siren: str, label: str, skip_load=False, skip_r2gg=False, skip_dump=False):
    """Traite un EPCI complet : LOAD → R2GG → DUMP."""
    print(f"\n{'='*60}")
    print(f"  EPCI: {label} ({siren})")
    print(f"{'='*60}")

    bbox = get_epci_bbox(siren)
    print(f"  BBOX (WGS84): {bbox}")

    # Step 1: LOAD
    if not skip_load:
        print(f"\n  [STEP 1/3] Chargement des tables source...")
        load_epci_tables(siren)
    else:
        print(f"\n  [STEP 1/3] SKIP load (tables déjà chargées)")

    # Step 2+3: R2GG
    if not skip_r2gg:
        print(f"\n  [STEP 2/3] Génération du graphe r2gg...")
        config_path = generate_r2gg_configs(siren, bbox)
        print(f"  Config: {config_path}")
        run_r2gg(config_path)
        verify_r2gg_tables(siren)
    else:
        print(f"\n  [STEP 2/3] SKIP r2gg")

    # Step 4: DUMP
    if not skip_dump:
        print(f"\n  [STEP 3/3] Export SQL dump...")
        dump_routing_tables(siren)
    else:
        print(f"\n  [STEP 3/3] SKIP dump")

    print(f"\n  ✓ EPCI {label} terminé !")


def main():
    parser = argparse.ArgumentParser(
        description="Génération des Gold Dumps pgRouting par EPCI (instructeur)"
    )
    parser.add_argument("--all", action="store_true", help="Générer pour tous les EPCIs")
    parser.add_argument("--epci", help="Nom ou SIREN d'un EPCI spécifique")
    parser.add_argument("--skip-load", action="store_true", help="Sauter l'étape de chargement des parquets")
    parser.add_argument("--skip-r2gg", action="store_true", help="Sauter l'étape r2gg (utile si déjà fait)")
    parser.add_argument("--skip-dump", action="store_true", help="Sauter l'export pg_dump")
    parser.add_argument("--load-only", action="store_true", help="Ne faire que le chargement des parquets")
    parser.add_argument("--r2gg-only", action="store_true", help="Ne faire que r2gg (load + pivot + pgr)")
    parser.add_argument("--dump-only", action="store_true", help="Ne faire que l'export pg_dump")
    args = parser.parse_args()

    # Résoudre les flags
    skip_load = args.skip_load
    skip_r2gg = args.skip_r2gg
    skip_dump = args.skip_dump

    if args.load_only:
        skip_r2gg = skip_dump = True
    elif args.r2gg_only:
        skip_dump = True
    elif args.dump_only:
        skip_load = skip_r2gg = True

    # Déterminer les EPCIs à traiter
    if args.all:
        targets = SELECTED_EPCIS
    elif args.epci:
        query = args.epci
        if query.isdigit() and len(query) == 9:
            label = SELECTED_EPCIS.get(query, "")
            targets = {query: label}
        else:
            matches = {s: l for s, l in SELECTED_EPCIS.items() if query.lower() in l.lower()}
            if not matches:
                print(f"Erreur: '{query}' ne correspond à aucun EPCI")
                print("EPCIs disponibles :")
                for s, l in SELECTED_EPCIS.items():
                    print(f"  {s} — {l}")
                return
            targets = matches
    else:
        parser.error("--all ou --epci requis")
        return

    print(f"[ADMIN] Gold Dumps — {len(targets)} EPCI(s) à traiter")
    print(f"  Skip load: {skip_load} | Skip r2gg: {skip_r2gg} | Skip dump: {skip_dump}")

    t_start = time.time()
    errors = []

    for siren, label in targets.items():
        try:
            process_epci(siren, label, skip_load, skip_r2gg, skip_dump)
        except Exception as e:
            print(f"\n  ✗ ERREUR sur {label}: {e}")
            errors.append((siren, label, str(e)))

    dt = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"[ADMIN] Terminé en {dt:.0f}s")
    if errors:
        print(f"  ⚠ {len(errors)} erreur(s):")
        for s, l, err in errors:
            print(f"    {s} {l}: {err}")
    else:
        print(f"  ✓ Tous les EPCIs traités avec succès")


if __name__ == "__main__":
    main()
