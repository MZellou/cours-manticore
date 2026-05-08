"""
00_setup.py — Chargement des données BDTOPO par EPCI
===================================================
Extrait les données d'un EPCI depuis les fichiers Parquet source
et les charge dans PostGIS.

Usage :
    python scripts/00_setup.py --list-epci
    python scripts/00_setup.py --epci "Brest Métropole"
    python scripts/00_setup.py --epci 242900314 --source /media/stores/cifs/...

Le script utilise data/epci.parquet pour trouver la géométrie de l'EPCI.
Les tables BDTOPO sont filtrées par la BBOX de l'EPCI.
"""

import argparse
import os
import subprocess
import sys
import time

import pandas as pd
import psycopg2
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from psycopg2.extras import execute_values
from shapely import prepared, wkb
from shapely.geometry import Point, box

# =============================================================================
# CONFIG
# =============================================================================

DEFAULT_SOURCE = "data/poi_source"
LOCAL_DATA = "data"

# Centrales nucléaires absentes de BDTOPO — injectées comme POIs custom
# (lon, lat, nom, puissance_MW)
NUCLEAR_PLANTS = [
    (2.14, 51.0, "Centrale nucléaire de Gravelines", 5460),
    (-1.85, 49.55, "Centrale nucléaire de Flamanville", 2660),
    (6.25, 49.42, "Centrale nucléaire de Cattenom", 5200),
    (4.82, 50.08, "Centrale nucléaire de Chooz", 3010),
    (0.65, 46.45, "Centrale nucléaire de Civaux", 3618),
    (4.65, 44.60, "Centrale nucléaire de Cruas-Meysse", 3600),
    (1.22, 49.97, "Centrale nucléaire de Penly", 4400),
    (4.75, 44.35, "Centrale nucléaire du Tricastin", 3640),
    (0.87, 47.06, "Centrale nucléaire de Chinon", 3620),
    (-0.78, 46.72, "Centrale nucléaire de Saint-Laurent", 1840),
    (0.95, 48.45, "Centrale nucléaire de Nogent", 2660),
    (3.12, 46.73, "Centrale nucléaire de Dampierre", 2160),
    (-1.20, 47.36, "Centrale nucléaire de Belleville", 2620),
    (4.93, 49.84, "Centrale nucléaire de Chooz-B", 3010),
    (5.37, 43.38, "Centrale nucléaire de Golfech", 2620),
]

TARGET_TABLES = [
    "aerodrome",
    "batiment",
    "construction_lineaire",
    "construction_ponctuelle",
    "construction_surfacique",
    "cours_d_eau",
    "detail_hydrographique",
    "detail_orographique",
    "foret_publique",
    "equipement_de_transport",
    "ligne_electrique",
    "parc_ou_reserve",
    "piste_d_aerodrome",
    "plan_d_eau",
    "poste_de_transformation",
    "pylone",
    "surface_hydrographique",
    "troncon_de_route",
    "troncon_de_voie_ferree",
    "zone_d_activite_ou_d_interet",
    "zone_de_vegetation",
    "non_communication",
]

# Mapping table -> cols à garder (économie de volume)
KEEP_COLS = {
    "batiment": [
        "fid",
        "cleabs",
        "nature",
        "usage_1",
        "usage_2",
        "etat_de_l_objet",
        "geometrie",
        "geometrie_bbox",
    ],
    "troncon_de_route": [
        "fid",
        "cleabs",
        "nature",
        "nom_collaboratif_gauche",
        "nom_collaboratif_droite",
        "importance",
        "fictif",
        "position_par_rapport_au_sol",
        "nombre_de_voies",
        "largeur_de_chaussee",
        "sens_de_circulation",
        "vitesse_moyenne_vl",
        "restriction_de_hauteur",
        "restriction_de_poids_total",
        "restriction_de_poids_par_essieu",
        "restriction_de_largeur",
        "restriction_de_longueur",
        "matieres_dangereuses_interdites",
        "geometrie",
        "geometrie_bbox",
    ],
    "construction_lineaire": [
        "fid",
        "cleabs",
        "nature",
        "nature_detaillee",
        "toponyme",
        "importance",
        "etat_de_l_objet",
        "geometrie",
        "geometrie_bbox",
    ],
    "cours_d_eau": [
        "fid",
        "cleabs",
        "code_hydrographique",
        "toponyme",
        "statut",
        "influence_de_la_maree",
        "caractere_permanent",
        "geometrie",
        "geometrie_bbox",
    ],
    "zone_d_activite_ou_d_interet": [
        "fid",
        "cleabs",
        "categorie",
        "nature",
        "nature_detaillee",
        "toponyme",
        "importance",
        "nom_commercial",
        "geometrie",
        "geometrie_bbox",
    ],
    "zone_de_vegetation": [
        "fid",
        "cleabs",
        "nature",
        "nature_detaillee",
        "etat_de_l_objet",
        "geometrie",
        "geometrie_bbox",
    ],
}

# =============================================================================
# HELPERS
# =============================================================================


def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGIS_HOST", "localhost"),
        port=os.getenv("POSTGIS_PORT", 5432),
        dbname=os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        user=os.getenv("POSTGIS_USER", "postgres"),
        password=os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    )


def list_epcis():
    df = pd.read_parquet(
        f"{LOCAL_DATA}/epci.parquet", columns=["code_siren", "nom_officiel"]
    )
    print(f"\n{'SIREN':<15} | {'NOM EPCI'}")
    print("-" * 50)
    for _, row in df.sort_values("nom_officiel").iterrows():
        print(f"{row.code_siren:<15} | {row.nom_officiel}")


def get_epci_info(query):
    df = pd.read_parquet(f"{LOCAL_DATA}/epci.parquet")
    # Recherche par SIREN exact (clé canonique), puis fallback nom
    if query.isdigit() and len(query) == 9:
        res = df[df["code_siren"] == query]
    else:
        res = df[df["nom_officiel"].str.contains(query, case=False, na=False)]
    if res.empty:
        raise ValueError(f"EPCI '{query}' non trouvé.")
    if len(res) > 1:
        print(
            f"[WARNING] Plusieurs EPCI trouvés pour '{query}', on prend le premier : {res.iloc[0]['nom_officiel']}"
        )

    row = res.iloc[0]
    geom = wkb.loads(row["geometrie"])
    bbox = row["geometrie_bbox"]  # {'xmin':..., 'ymin':..., 'xmax':..., 'ymax':...}
    return (
        row["nom_officiel"],
        row["code_siren"],
        geom,
        (bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]),
    )


def filter_row_groups(pf, xmin, ymin, xmax, ymax):
    kept = []
    for rg_idx in range(pf.metadata.num_row_groups):
        table = pf.read_row_group(rg_idx, columns=["geometrie_bbox"])
        col = table.column("geometrie_bbox")
        rg_xmin = pc.min(pc.struct_field(col, "xmin")).as_py()
        rg_xmax = pc.max(pc.struct_field(col, "xmax")).as_py()
        rg_ymin = pc.min(pc.struct_field(col, "ymin")).as_py()
        rg_ymax = pc.max(pc.struct_field(col, "ymax")).as_py()
        if (
            rg_xmin is not None
            and rg_xmin < xmax
            and rg_xmax > xmin
            and rg_ymin < ymax
            and rg_ymax > ymin
        ):
            kept.append(rg_idx)
    return kept


def create_table(conn, table_name, arrow_schema, cols_to_keep):
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        col_defs = []
        for name, typ in zip(arrow_schema.names, arrow_schema.types):
            if name in ("geometrie", "geometrie_bbox") or (
                cols_to_keep and name not in cols_to_keep
            ):
                continue
            pg_type = "TEXT"
            if "int64" in str(typ):
                pg_type = "BIGINT"
            elif "int" in str(typ):
                pg_type = "INTEGER"
            elif "float" in str(typ) or "double" in str(typ):
                pg_type = "DOUBLE PRECISION"
            elif "bool" in str(typ):
                pg_type = "BOOLEAN"
            col_defs.append(f'"{name}" {pg_type}')

        # Cas particulier pour non_communication qui n'a pas forcément de géométrie
        if "geometrie" in arrow_schema.names:
            col_defs.append('"geometrie" GEOMETRY(Geometry, 2154)')
            cur.execute(f"CREATE TABLE {table_name} ({', '.join(col_defs)});")
            cur.execute(
                f"CREATE INDEX {table_name}_geom_idx ON {table_name} USING GIST (geometrie);"
            )
        else:
            cur.execute(f"CREATE TABLE {table_name} ({', '.join(col_defs)});")
    conn.commit()


def insert_batch(conn, table_name, table_arrow, epci_geom_prepared, cols_to_keep,
                  skip_spatial_filter=False):
    df = table_arrow.to_pandas()

    has_geom = "geometrie" in df.columns

    if has_geom and not skip_spatial_filter:
        # Filtrage exact par géométrie (shapely)
        # On convertit les bytes WKB en objets shapely
        df["_shapely"] = df["geometrie"].apply(lambda x: wkb.loads(x) if x else None)

        # On ne garde que ce qui intersecte l'EPCI
        df = df[
            df["_shapely"].apply(
                lambda x: epci_geom_prepared.intersects(x) if x else False
            )
        ]

    if df.empty:
        return 0

    cols = [
        c
        for c in df.columns
        if c not in ("geometrie", "geometrie_bbox", "_shapely")
        and (not cols_to_keep or c in cols_to_keep)
    ]

    data = []
    for _, row in df.iterrows():
        vals = [row[c] for c in cols]
        if has_geom:
            # On passe la géométrie en WKB binaire pour PostGIS
            vals.append(psycopg2.Binary(row["geometrie"]))
        data.append(tuple(vals))

    quoted_cols = [f'"{c}"' for c in cols]
    if has_geom:
        insert_sql = (
            f"INSERT INTO {table_name} ({', '.join(quoted_cols)}, geometrie) VALUES %s"
        )
    else:
        insert_sql = f"INSERT INTO {table_name} ({', '.join(quoted_cols)}) VALUES %s"

    with conn.cursor() as cur:
        if has_geom:
            tmpl = "(" + ", ".join(["%s"] * len(cols)) + ", ST_Transform(ST_Force2D(ST_GeomFromWKB(%s, 4326)), 2154))"
            execute_values(cur, insert_sql, data, template=tmpl, page_size=500)
        else:
            execute_values(cur, insert_sql, data, page_size=500)
    conn.commit()
    return len(df)


def load_ontology(conn):
    print("\n[ONTOLOGY] Chargement de la hiérarchie BDTOPO...")

    # On crée une table simple : id, name, obj_type, parent_id
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS bdtopo_ontology CASCADE;")
        cur.execute("""
            CREATE TABLE bdtopo_ontology (
                id SERIAL PRIMARY KEY,
                name TEXT,
                obj_type TEXT,
                parent_id INTEGER
            );
        """)
    conn.commit()

    # 1. Database (Level 1)
    df_db = pd.read_parquet(f"{LOCAL_DATA}/ontologie/bdtopo_database.parquet")
    db_map = {}  # name -> id
    with conn.cursor() as cur:
        for name in df_db["name"].unique():
            cur.execute(
                "INSERT INTO bdtopo_ontology (name, obj_type) VALUES (%s, 'Database') RETURNING id;",
                (name,),
            )
            db_map[name] = cur.fetchone()[0]

    # 2. Objects (Level 2)
    df_obj = pd.read_parquet(f"{LOCAL_DATA}/ontologie/bdtopo_objects.parquet")
    obj_map = {}  # name -> id
    with conn.cursor() as cur:
        for _, row in df_obj.iterrows():
            parent_id = db_map.get(row["parent_db_name"])
            cur.execute(
                "INSERT INTO bdtopo_ontology (name, obj_type, parent_id) VALUES (%s, 'Object', %s) RETURNING id;",
                (row["name"], parent_id),
            )
            obj_map[row["name"]] = cur.fetchone()[0]

    # 3. Details (Level 3)
    df_det = pd.read_parquet(f"{LOCAL_DATA}/ontologie/bdtopo_details.parquet")
    with conn.cursor() as cur:
        for _, row in df_det.iterrows():
            parent_id = obj_map.get(row["parent_obj_name"])
            cur.execute(
                "INSERT INTO bdtopo_ontology (name, obj_type, parent_id) VALUES (%s, 'Detail', %s);",
                (row["name"], parent_id),
            )

    conn.commit()
    print("  [OK] Ontologie chargée.")


def inject_custom_pois(conn, epci_geom_prepared):
    """Injecte les centrales nucléaires qui tombent dans l'EPCI comme POIs custom."""
    print("\n[CUSTOM POIS] Injection des centrales nucléaires...")
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS mission_custom_pois CASCADE;")
        cur.execute("""
            CREATE TABLE mission_custom_pois (
                id SERIAL PRIMARY KEY,
                nom TEXT,
                type TEXT,
                puissance_mw INTEGER,
                geometrie GEOMETRY(Point, 4326)
            );
        """)
    conn.commit()

    from shapely.ops import transform

    # WGS84 -> Lambert-93
    proj_wgs84 = "EPSG:4326"
    proj_l93 = "EPSG:2154"
    import pyproj

    transformer = pyproj.Transformer.from_crs(
        proj_wgs84, proj_l93, always_xy=True
    ).transform

    count = 0
    with conn.cursor() as cur:
        for lon, lat, nom, puissance in NUCLEAR_PLANTS:
            pt = Point(lon, lat)
            if epci_geom_prepared.intersects(pt):
                pt_l93 = transform(transformer, pt)
                cur.execute(
                    "INSERT INTO mission_custom_pois (nom, type, puissance_mw, geometrie) VALUES (%s, %s, %s, %s)",
                    (nom, "Centrale nucléaire", puissance, pt_l93.wkb),
                )
                print(f"  → {nom} ({puissance} MW)")
                count += 1
    conn.commit()
    print(f"  [OK] {count} centrale(s) injectée(s) dans l'EPCI.")


def load_gold_dumps(siren):
    """Charge les Gold Dumps pgRouting pré-calculés dans PostGIS.

    Les dumps sont générés par admin_generate_gold_dumps.py et contiennent
    les tables ways, ways_vertices_pgr et turn_restrictions dans un schéma
    pgr_{siren}. On les restore dans le schéma public pour le TD.
    """
    dump_path = f"{LOCAL_DATA}/gold_dumps/{siren}/ways.sql"
    if not os.path.exists(dump_path):
        print(f"\n[GOLD DUMPS] Fichier absent: {dump_path}")
        print("  → Le routage pgRouting ne sera pas disponible.")
        print("  → Générer les dumps: python scripts/admin_generate_gold_dumps.py --epci {siren}")
        return False

    print(f"\n[GOLD DUMPS] Restauration depuis {dump_path}...")
    env = {
        "PGHOST": os.getenv("POSTGIS_HOST", "localhost"),
        "PGPORT": os.getenv("POSTGIS_PORT", "5432"),
        "PGDATABASE": os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        "PGUSER": os.getenv("POSTGIS_USER", "postgres"),
        "PGPASSWORD": os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    }

    # Le dump contient les tables dans le schéma pgr_{siren}
    # On restore tel quel — les scripts de routage utilisent le schéma pgr_
    result = subprocess.run(
        ["psql", "-f", dump_path],
        env={**os.environ, **env},
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  ✗ Erreur pg_restore: {result.stderr[:500]}")
        return False

    # Vérifier les comptages
    conn = get_conn()
    schema = f"pgr_{siren}"
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(f"SELECT count(*) FROM {schema}.ways")
                n_ways = cur.fetchone()[0]
                cur.execute(f"SELECT count(*) FROM {schema}.ways_vertices_pgr")
                n_verts = cur.fetchone()[0]
                print(f"  ✓ Restauré: {n_ways} ways, {n_verts} vertices (schéma {schema})")
            except Exception as e:
                print(f"  ⚠ Tables restaurées mais vérification impossible: {e}")
                return True
    finally:
        conn.close()

    return True


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epci", help="Nom ou SIREN de l'EPCI")
    parser.add_argument(
        "--list-epci", action="store_true", help="Lister les EPCI disponibles"
    )
    parser.add_argument(
        "--source", default=DEFAULT_SOURCE, help="Dossier source des Parquets BDTOPO"
    )
    parser.add_argument(
        "--skip-spatial-filter", action="store_true",
        help="Skip shapely filtering (use when source is already BBOX-filtered)"
    )
    parser.add_argument(
        "--skip-gold-dumps", action="store_true",
        help="Skip gold dumps restoration"
    )
    args = parser.parse_args()

    if args.list_epci:
        list_epcis()
        return

    if not args.epci:
        print("Erreur: --epci est requis (ou --list-epci)")
        return

    # 1. Info EPCI
    name, siren, geom, bbox = get_epci_info(args.epci)
    print(f"\n[MANTICORE] Préparation de l'EPCI : {name} ({siren})")
    print(f"BBOX: {bbox}")

    prep_geom = prepared.prep(geom)
    skip_sf = args.skip_spatial_filter
    conn = get_conn()

    # 1.5 Ontologie
    load_ontology(conn)

    # 1.6 Custom POIs (centrales nucléaires)
    inject_custom_pois(conn, prep_geom)

    # 2. Boucle sur les tables
    total = 0
    for table_name in TARGET_TABLES:
        p_path = f"{args.source}/{table_name}.parquet"
        if not os.path.exists(p_path):
            print(f"  [SKIP] {table_name} (fichier absent)")
            continue

        t0 = time.time()
        pf = pq.ParquetFile(p_path)

        cols_to_keep = KEEP_COLS.get(table_name)
        if skip_sf:
            rg_ids = list(range(pf.metadata.num_row_groups))
        else:
            rg_ids = filter_row_groups(pf, *bbox)

        # Création table
        create_table(conn, table_name, pf.schema_arrow, cols_to_keep)

        # Lecture et insertion
        inserted = 0
        for rg_id in rg_ids:
            table_arrow = pf.read_row_group(
                rg_id,
                columns=cols_to_keep + ["geometrie"]
                if cols_to_keep and "geometrie" in pf.schema_arrow.names
                else (cols_to_keep if cols_to_keep else None),
            )
            inserted += insert_batch(
                conn, table_name, table_arrow, prep_geom, cols_to_keep,
                skip_spatial_filter=skip_sf
            )

        dt = time.time() - t0
        print(f"  [OK] {table_name:<30} | {inserted:>6} lignes | {dt:.1f}s")
        total += inserted

    conn.close()
    print(f"\n[FINISH] Opération terminée. Total: {total} objets chargés.")

    # 3. Gold Dumps (pgRouting)
    if not args.skip_gold_dumps:
        load_gold_dumps(siren)
    else:
        print("\n[GOLD DUMPS] Skip (--skip-gold-dumps)")


if __name__ == "__main__":
    main()
