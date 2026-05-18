"""
Phase 3 — Benchmark SQL vs Cypher + Carte de situation
=====================================================
Compare les performances de WITH RECURSIVE (SQL) vs Cypher (Neo4j)
sur la même requête ontologique, puis génère la carte finale.

Usage : python scripts/04_benchmark_comparison.py --role logistique
"""

import argparse
import os
import time
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

ROLES = ["attaque", "defense", "logistique"]

def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGIS_HOST", "localhost"),
        port=os.getenv("POSTGIS_PORT", 5432),
        dbname=os.getenv("POSTGIS_DB", "bdtopo_manticore"),
        user=os.getenv("POSTGIS_USER", "postgres"),
        password=os.getenv("POSTGIS_PASSWORD", "manticore2026"),
    )

def get_neo_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "manticore2026")
    return GraphDatabase.driver(uri, auth=(user, password))

def print_section(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")

# =============================================================================
# BENCHMARK : SQL WITH RECURSIVE vs Cypher variable-length paths
# =============================================================================

def benchmark_ontology(pg_conn, neo_driver):
    print_section("BENCHMARK — SQL WITH RECURSIVE vs Cypher")

    root = "Tronçon de route"

    # --- SQL ---
    sql_query = f"""
        WITH RECURSIVE hierarchy AS (
            SELECT id, name, obj_type, parent_id, 0 AS depth
            FROM bdtopo_ontology WHERE name = '{root}'
            UNION ALL
            SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
            FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id
        )
        SELECT count(*) FROM hierarchy;
    """
    t0 = time.time()
    try:
        with pg_conn.cursor() as cur:
            cur.execute(sql_query)
            sql_result = cur.fetchone()[0]
        sql_time = (time.time() - t0) * 1000
    except psycopg2.Error as e:
        print(f"  [SQL ERREUR] {e}")
        sql_time, sql_result = None, None

    # --- Cypher ---
    # Labels: :ClasseOntologie avec obj_type ∈ {Database, Object, Detail}.
    # Tronçon de route est un Database → on remonte n'importe quel descendant
    # (Object au-dessus, Detail au-dessus encore) jusqu'à la racine nommée.
    cypher_query = """
        MATCH path = (n:ClasseOntologie)-[:EST_SOUS_TYPE_DE*1..3]->
                     (root:ClasseOntologie {name: $root})
        RETURN count(path) AS count
    """
    t0 = time.time()
    try:
        with neo_driver.session() as session:
            result = session.run(cypher_query, root=root)
            records = list(result)
            neo_time = (time.time() - t0) * 1000
        neo_count = records[0]["count"] if records else 0
    except Exception as e:
        print(f"  [CYPHER ERREUR] {e}")
        neo_time, neo_count = None, 0

    # --- Résultats ---
    print(f"\n  Requête : tous les sous-types de '{root}'")
    print(f"  {'Moteur':<15} | {'Temps (ms)':>10} | {'Résultats':>10}")
    print(f"  {'-'*42}")
    sql_str = f"{sql_time:.2f}" if sql_time is not None else "---"
    neo_str = f"{neo_time:.2f}" if neo_time is not None else "---"
    print(f"  {'PostgreSQL':<15} | {sql_str:>10} | {sql_result if sql_result is not None else 'N/A':>10}")
    print(f"  {'Neo4j':<15} | {neo_str:>10} | {neo_count:>10}")

    if sql_time and neo_time and neo_time > 0 and sql_time > 0:
        ratio = sql_time / neo_time
        print(f"\n  → SQL est {ratio:.1f}x {'plus lent' if ratio > 1 else 'plus rapide'} que Cypher")

    # --- EXPLAIN ANALYZE SQL ---
    print("\n  --- EXPLAIN ANALYZE (SQL) ---")
    try:
        with pg_conn.cursor() as cur:
            cur.execute(f"EXPLAIN (ANALYZE, BUFFERS) {sql_query}")
            for row in cur.fetchall():
                print(f"    {row[0]}")
    except Exception:
        pass

    # --- PROFILE Cypher ---
    print("\n  --- PROFILE (Cypher) ---")
    try:
        with neo_driver.session() as session:
            result = session.run(f"PROFILE {cypher_query}", root=root)
            list(result)  # drain rows avant consume()
            summary = result.consume()
            plan = summary.profile
        if plan:
            print(f"    Operator racine : {plan.get('operatorType', 'n/a')}")
            print(f"    DB hits totaux  : {plan.get('dbHits', 'n/a')}")
            print(f"    Rows produites  : {plan.get('rows', 'n/a')}")
        else:
            print("    Profile vide (vérifier Neo4j Browser pour le plan détaillé).")
    except Exception as e:
        print(f"    [ERREUR] {e}")

# =============================================================================
# BENCHMARK SPATIAL : ST_Intersects SQL vs distance Neo4j
# =============================================================================

def benchmark_spatial(pg_conn, neo_driver):
    print_section("BENCHMARK — Jointures spatiales SQL")

    query = """
        SELECT count(*) FROM mission_pois p
        WHERE EXISTS (
            SELECT 1 FROM troncon_de_route r
            WHERE ST_DWithin(p.geom, r.geometrie, 500)
        )
    """
    t0 = time.time()
    try:
        with pg_conn.cursor() as cur:
            cur.execute(query)
            count = cur.fetchone()[0]
        elapsed = (time.time() - t0) * 1000
        print(f"  POIs à < 500m d'une route : {count} ({elapsed:.1f} ms)")
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e}")

# =============================================================================
# CARTE DE SITUATION
# =============================================================================

def generate_situation_map(
    epci: str,
    layers: list = ("attaque", "defense", "logistique"),
    output_path: str | None = None,
    basemap: bool = True,
) -> str:
    """Génère la Carte de Situation Commune pour un EPCI.

    Args:
        epci: Nom ou SIREN (9 chiffres) de l'EPCI.
        layers: Rôles à afficher, dans l'ordre de superposition (dernier = dessus).
        output_path: Chemin PNG de sortie. Défaut : data/carte_situation_{epci}.png
        basemap: Afficher un fond de carte CartoDB Positron via contextily.

    Returns:
        Chemin absolu du fichier PNG généré.
    """
    if output_path is None:
        output_path = f"data/carte_situation_{epci}.png"

    # Mapping legacy rôles pre-refactor → logistique
    LEGACY = {"ravitaillement": "logistique", "energie": "logistique"}

    pg_conn = psycopg2.connect(
        host=os.getenv("PG_HOST", os.getenv("POSTGIS_HOST", "localhost")),
        port=os.getenv("PG_PORT", os.getenv("POSTGIS_PORT", 5432)),
        dbname=os.getenv("PG_DB", os.getenv("POSTGIS_DB", "bdtopo_manticore")),
        user=os.getenv("PG_USER", os.getenv("POSTGIS_USER", "postgres")),
        password=os.getenv("PG_PASSWORD", os.getenv("POSTGIS_PASSWORD", "manticore2026")),
    )
    try:
        import geopandas as gpd
        from shapely import wkb
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Résolution bbox EPCI
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT ST_AsText(ST_Extent(geometrie)) FROM epci WHERE code_siren = %s OR nom_officiel ILIKE %s",
                (epci, epci),
            )
            bbox_wkt = cur.fetchone()[0]

        # POIs avec mapping legacy
        with pg_conn.cursor() as cur:
            cur.execute("""
                SELECT role, nom, ST_AsBinary(geom)
                FROM mission_pois
                WHERE geom IS NOT NULL
                  AND (%s IS NULL OR ST_Within(geom, ST_SetSRID(ST_GeomFromText(%s), 2154)))
            """, (bbox_wkt, bbox_wkt))
            rows = cur.fetchall()
    finally:
        pg_conn.close()

    if not rows:
        print("  [SKIP] Aucun POI à cartographier.")
        return os.path.abspath(output_path)

    # Normalisation des rôles legacy
    records = []
    for role_val, nom, geom_bytes in rows:
        role_norm = LEGACY.get(role_val, role_val)
        records.append({"role": role_norm, "nom": nom, "geometry": wkb.loads(bytes(geom_bytes))})

    gdf = gpd.GeoDataFrame(records, crs="EPSG:2154").to_crs(epsg=3857)

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Couches : logistique < defense < attaque (zorder croissant)
    layer_styles = {
        "logistique": {"color": "#2196F3", "marker": "s", "zorder": 1},
        "defense":    {"color": "#4CAF50", "marker": "^", "zorder": 2},
        "attaque":    {"color": "#F44336", "marker": "X", "zorder": 3},
    }
    for layer in layers:
        style = layer_styles.get(layer, {"color": "grey", "marker": "o", "zorder": 1})
        mask = gdf["role"] == layer
        if mask.any():
            gdf[mask].plot(
                ax=ax, color=style["color"], marker=style["marker"],
                markersize=30, alpha=0.7, label=layer.upper(), zorder=style["zorder"],
            )

    # Fond de carte optionnel
    if basemap:
        try:
            import contextily as ctx
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        except Exception:
            pass  # contextily absent ou erreur réseau — on continue sans fond

    ax.set_title(f"Situation tactique — {epci}", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.set_axis_off()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    abs_path = os.path.abspath(output_path)
    print(f"  → Carte sauvegardée : {abs_path}")
    return abs_path


def generate_situation_map_legacy(pg_conn, role, output_path="data/carte_situation.png"):
    """Wrapper déprécié — utiliser generate_situation_map(epci=...) à la place."""
    import warnings
    warnings.warn(
        "generate_situation_map(pg_conn, role, ...) est déprécié. "
        "Utiliser generate_situation_map(epci=...) à la place.",
        DeprecationWarning, stacklevel=2,
    )
    return generate_situation_map(epci=role, output_path=output_path)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epci", required=True, help="Nom ou SIREN de l'EPCI")
    parser.add_argument("--map", default=None, help="Chemin carte PNG (défaut: data/carte_situation_<epci>.png)")
    parser.add_argument("--no-basemap", action="store_true", help="Désactiver le fond de carte contextily")
    args = parser.parse_args()

    print(f"""
  ============================================================
   OPÉRATION MANTICORE — Phase 3 : Benchmark & Carte
   EPCI : {args.epci}
  ============================================================
    """)

    pg_conn = get_pg_conn()
    neo_driver = get_neo_driver()
    try:
        benchmark_ontology(pg_conn, neo_driver)
        benchmark_spatial(pg_conn, neo_driver)
    finally:
        pg_conn.close()
        neo_driver.close()

    generate_situation_map(
        epci=args.epci,
        output_path=args.map,
        basemap=not args.no_basemap,
    )
