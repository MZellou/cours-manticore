"""
Phase 2 — Cartographie : Migration vers Neo4j
=============================================
Migre l'ontologie BDTOPO + les POIs de la phase 1 vers Neo4j.
Inclut des exemples APOC pour le routage multi-POIs.

Usage : python scripts/02_migrate_to_neo4j.py
"""

import os
import psycopg2
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

LOCAL_DATA = "data/ontologie"

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

# =============================================================================
# MIGRATION ONTOLOGIE
# =============================================================================

def clear_db(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def load_databases(tx, df):
    # parent_db_name dans les niveaux Object/Detail référence le sql_name → on l'index aussi.
    tx.run("""
        UNWIND $rows AS row
        MERGE (d:ClasseOntologie {sql_name: row.sql_name})
        SET d.name = row.name, d.obj_type = 'Database', d.definition = row.definition
    """, rows=df.to_dict('records'))

def load_objects(tx, df):
    # 50 noms d'Object sont dupliqués entre Databases (Aqueduc, Pont, …) → MERGE composite
    # {sql_name + name} disambiguates. parent_db_name = sql_name de la Database parente.
    tx.run("""
        UNWIND $rows AS row
        MERGE (o:ClasseOntologie {sql_name: row.sql_name, name: row.name, obj_type: 'Object'})
        SET o.definition = row.definition
        WITH o, row
        MATCH (p:ClasseOntologie {sql_name: row.parent_db_name, obj_type: 'Database'})
        MERGE (o)-[:EST_SOUS_TYPE_DE]->(p)
    """, rows=df.to_dict('records'))

def load_details(tx, df):
    # Detail.parent_obj_name référence le name humain de l'Object parent.
    # Le sql_name (table) du Detail est le même que celui de son Object parent → on
    # restreint le MATCH par sql_name + obj_type pour éviter les ambigüités multi-Database.
    tx.run("""
        UNWIND $rows AS row
        MERGE (d:ClasseOntologie {sql_name: row.sql_name, name: row.name, obj_type: 'Detail'})
        SET d.definition = row.definition
        WITH d, row
        MATCH (p:ClasseOntologie {sql_name: row.sql_name, name: row.parent_obj_name, obj_type: 'Object'})
        MERGE (d)-[:EST_SOUS_TYPE_DE]->(p)
    """, rows=df.to_dict('records'))

# =============================================================================
# MIGRATION POIs
# =============================================================================

def load_pois_from_postgis(tx, pois):
    """Charge les POIs depuis mission_pois (PostGIS) dans Neo4j.

    Utilise une clé composite {cleabs, role} pour éviter les collisions :
    un même objet BDTOPO (ex: gendarmerie) peut apparaître dans mission_pois
    pour plusieurs rôles (attaque + défense). MERGE sur cleabs seul écrasait
    le role du précédent — on créait 1 nœud au lieu de 2.
    """
    tx.run("""
        UNWIND $pois AS p
        MERGE (poi:POI {cleabs: p.cleabs, role: p.role})
        SET poi.source = p.source,
            poi.categorie = p.categorie,
            poi.nature = p.nature,
            poi.nom = p.nom,
            poi.lat = p.lat,
            poi.lon = p.lon
    """, pois=pois)

def create_distance_edges(tx, edges):
    """Crée les relations de distance entre POIs proches."""
    tx.run("""
        UNWIND $edges AS e
        MATCH (a:POI {cleabs: e.from}), (b:POI {cleabs: e.to})
        MERGE (a)-[r:DISTANCE {meters: e.distance}]->(b)
    """, edges=edges)

# =============================================================================
# EXEMPLES APOC
# =============================================================================

def demo_apoc_queries(session):
    """Montre les requêtes APOC utiles pour la phase 2."""
    print("\n  --- Requêtes APOC à explorer ---\n")

    # 1. Sous-types par pattern matching
    result = session.run("""
        MATCH path = (n:ClasseOntologie)-[:EST_SOUS_TYPE_DE*]->
                     (root:ClasseOntologie {name: 'Tronçon de route', obj_type: 'Database'})
        RETURN [node IN nodes(path) | node.name] AS hierarchy
        LIMIT 5
    """)
    for r in result:
        print(f"  [PATH] {' → '.join(r['hierarchy'])}")

    # 2. Tous les POIs par rôle
    result = session.run("""
        MATCH (p:POI)
        RETURN p.role AS role, count(*) AS count
        ORDER BY count DESC
    """)
    print(f"\n  POIs dans Neo4j :")
    for r in result:
        print(f"    {r['role']}: {r['count']}")

    # 3. Exemple Dijkstra APOC (si > 1 POI)
    result = session.run("""
        MATCH (a:POI), (b:POI)
        WHERE id(a) < id(b)
        WITH a, b LIMIT 1
        CALL apoc.algo.dijkstra(a, b, 'DISTANCE', 'meters') YIELD path, weight
        RETURN weight AS distance_m, [n IN nodes(path) | n.nom] AS route
    """)
    try:
        r = result.single()
        if r:
            print(f"\n  [DIJKSTRA APOC] Distance: {r['distance_m']}m, Route: {r['route']}")
    except Exception:
        print("  [APOC] apoc.algo.dijkstra non disponible ou pas assez de POIs.")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("""
  ============================================================
   OPÉRATION MANTICORE — Phase 2 : Migration Neo4j
  ============================================================
    """)

    neo_driver = get_neo_driver()
    pg_conn = get_pg_conn()

    try:
        with neo_driver.session() as session:
            # 1. Nettoyage + ontologie
            session.execute_write(clear_db)
            print("  → Base Neo4j nettoyée.")

            df_db = pd.read_parquet(f"{LOCAL_DATA}/bdtopo_database.parquet")
            session.execute_write(load_databases, df_db)

            df_obj = pd.read_parquet(f"{LOCAL_DATA}/bdtopo_objects.parquet")
            session.execute_write(load_objects, df_obj)

            df_det = pd.read_parquet(f"{LOCAL_DATA}/bdtopo_details.parquet")
            session.execute_write(load_details, df_det)
            print("  → Ontologie BDTOPO chargée.")

            # 2. POIs depuis PostGIS
            print("  → Migration des POIs depuis mission_pois...")
            with pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT role, source, cleabs, categorie, nature, nom,
                           ST_X(ST_Centroid(ST_Transform(geom, 4326))) AS lon,
                           ST_Y(ST_Centroid(ST_Transform(geom, 4326))) AS lat
                    FROM mission_pois
                    WHERE geom IS NOT NULL
                """)
                pois = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
            pg_conn.close()

            if pois:
                session.execute_write(load_pois_from_postgis, pois)
                print(f"  → {len(pois)} POIs chargés dans Neo4j.")

            # 3. Relations DISTANCE entre POIs proches (< 10km)
            # Batching with spatial pre-filter to avoid OOM on cross-product
            all_pois = session.run("MATCH (p:POI) WHERE p.lat IS NOT NULL RETURN elementId(p) AS eid").data()
            poi_ids = [r["eid"] for r in all_pois]
            batch_size = 100
            nb_rel = 0

            for i in range(0, len(poi_ids), batch_size):
                batch = poi_ids[i : i + batch_size]
                result = session.run("""
                    UNWIND $ids AS eid
                    MATCH (a:POI) WHERE elementId(a) = eid
                    MATCH (b:POI)
                    WHERE elementId(a) < elementId(b)
                      AND b.lat IS NOT NULL
                      AND abs(a.lat - b.lat) < 0.1
                      AND abs(a.lon - b.lon) < 0.15
                    WITH a, b,
                         toInteger(point.distance(
                             point({latitude: a.lat, longitude: a.lon}),
                             point({latitude: b.lat, longitude: b.lon})
                         )) AS dist_m
                    WHERE dist_m < 10000
                    MERGE (a)-[:DISTANCE {meters: dist_m}]->(b)
                    RETURN count(*) AS batch_count
                """, ids=batch)
                r = result.single()
                nb_rel += r["batch_count"] if r else 0
                if (i // batch_size) % 5 == 0:
                    print(f"    ... {i + len(batch)}/{len(poi_ids)} POIs traités, {nb_rel} relations")

            print(f"  → {nb_rel} relations DISTANCE créées (< 10km)")

            # 4. Démos APOC
            demo_apoc_queries(session)

        print("\n  [OK] Phase 2 — Migration terminée.")

    except Exception as e:
        print(f"\n  [ERREUR] {e}")
    finally:
        neo_driver.close()
        try:
            pg_conn.close()
        except Exception:
            pass
