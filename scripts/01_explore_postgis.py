"""
Phase 1 — Reconnaissance : Identifier les POIs critiques
========================================================
Pour chaque rôle (Attaque/Défense/Ravitaillement/Énergie), exécute les requêtes
SQL de sélection des POIs stratégiques dans l'EPCI, puis les clusterise.

Usage : python scripts/01_explore_postgis.py --role attaque
"""

import argparse
import os
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

ROLES = ["attaque", "defense", "ravitaillement", "energie"]

ROLE_QUERIES = {
    "attaque": """
        -- Cibles stratégiques : aérodromes, ports commerce, casernes, tours de contrôle
        SELECT 'aerodrome' AS source, cleabs, categorie, nature, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM aerodrome
        WHERE categorie IN ('Internationale', 'Nationale')

        UNION ALL

        SELECT 'equipement', cleabs, nature, nature_detaillee, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM equipement_de_transport
        WHERE nature = 'Port' AND nature_detaillee = 'Port de commerce'

        UNION ALL

        SELECT 'zone_militaire', cleabs, categorie, nature, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM zone_d_activite_ou_d_interet
        WHERE categorie = 'Administratif ou militaire'
          AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')

        UNION ALL

        SELECT 'tour_controle', cleabs, nature, nature_detaillee, NULL,
               ST_Force2D(geometrie) AS geom
        FROM construction_ponctuelle
        WHERE nature ILIKE 'Tour de contrôle%'
    """,
    "defense": """
        -- Points à protéger : hôpitaux, gendarmeries, gares, ponts, phares
        SELECT 'hopital', cleabs, categorie, nature, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM zone_d_activite_ou_d_interet
        WHERE nature IN ('Hôpital', 'Établissement hospitalier', 'Maison de retraite')

        UNION ALL

        SELECT 'gendarmerie', cleabs, categorie, nature, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM zone_d_activite_ou_d_interet
        WHERE categorie = 'Administratif ou militaire'
          AND nature IN ('Gendarmerie', 'Caserne')

        UNION ALL

        SELECT 'gare', cleabs, nature, nature_detaillee, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM equipement_de_transport
        WHERE nature ILIKE 'Gare%'

        UNION ALL

        SELECT 'pont', cleabs, nature, nature_detaillee, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM construction_surfacique
        WHERE nature = 'Pont'

        UNION ALL

        SELECT 'observation', cleabs, nature, nature_detaillee, NULL,
               ST_Force2D(geometrie) AS geom
        FROM construction_ponctuelle
        WHERE nature IN ('Phare', 'Tour de guet')
    """,
    "ravitaillement": """
        -- Flux logistiques : ports, gares fret, zones industrielles, réservoirs
        SELECT 'port', cleabs, nature, nature_detaillee, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM equipement_de_transport
        WHERE nature = 'Port'
          AND nature_detaillee IN ('Port de commerce', 'Port de pêche', 'Halte fluviale')

        UNION ALL

        SELECT 'gare_fret', cleabs, nature, nature_detaillee, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM equipement_de_transport
        WHERE nature IN ('Gare fret uniquement', 'Gare voyageurs et fret')

        UNION ALL

        SELECT 'zone_logistique', cleabs, categorie, nature, toponyme,
               ST_Force2D(geometrie) AS geom
        FROM zone_d_activite_ou_d_interet
        WHERE nature IN ('Zone industrielle', "Zone d'activités", 'Usine', 'Marché')

        UNION ALL

        SELECT 'reservoir', cleabs, nature, NULL, NULL,
               ST_Force2D(geometrie) AS geom
        FROM reservoir
        WHERE nature = 'Réservoir industriel'
    """,
    "energie": """
        -- Réseau énergétique : postes HT, lignes THT, éoliennes, barrages, oléoducs
        SELECT 'poste_ht', cleabs, nature, CAST(importance AS INTEGER) AS criticite, NULL,
               ST_Force2D(geometrie) AS geom
        FROM poste_de_transformation
        WHERE CAST(importance AS INTEGER) <= 3

        UNION ALL

        SELECT 'ligne_tht', cleabs, nature, voltage, NULL,
               ST_Force2D(geometrie) AS geom
        FROM ligne_electrique
        WHERE voltage IN ('400 kV', '225 kV')

        UNION ALL

        SELECT 'source_energie', cleabs, nature, nature_detaillee, NULL,
               ST_Force2D(geometrie) AS geom
        FROM construction_ponctuelle
        WHERE nature IN ('Éolienne', 'Transformateur', 'Cheminée')

        UNION ALL

        SELECT 'barrage', cleabs, nature, nature_detaillee, NULL,
               ST_Force2D(geometrie) AS geom
        FROM construction_surfacique
        WHERE nature = 'Barrage'

        UNION ALL

        SELECT 'oléoduc', cleabs, nature, NULL, NULL,
               ST_Force2D(geometrie) AS geom
        FROM canalisation
        WHERE nature = 'Hydrocarbures'

        UNION ALL

        SELECT 'stockage', cleabs, nature, NULL, NULL,
               ST_Force2D(geometrie) AS geom
        FROM reservoir
        WHERE nature = 'Réservoir industriel'

        UNION ALL

        SELECT 'centrale', id::TEXT, type, puissance_mw::TEXT, nom,
               geometrie AS geom
        FROM mission_custom_pois
    """,
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

def print_section(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")

# =============================================================================
# EXERCICE 1 — Ontologie hiérarchique (WITH RECURSIVE)
# =============================================================================

def ex1_ontologie_recursive(conn):
    print_section("EXERCICE 1 — WITH RECURSIVE : ontologie BDTOPO")

    query = """
        WITH RECURSIVE hierarchy AS (
            SELECT id, name, obj_type, parent_id, 0 AS depth
            FROM bdtopo_ontology
            WHERE name = 'Tronçon de route'
            UNION ALL
            SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
            FROM bdtopo_ontology AS child
            JOIN hierarchy AS h ON child.parent_id = h.id
        )
        SELECT depth, obj_type, name
        FROM hierarchy
        ORDER BY depth, name
        LIMIT 30;
    """
    t0 = time.time()
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    elapsed = (time.time() - t0) * 1000

    print(f"  Hiérarchie sous 'Tronçon de route' ({len(rows)} noeuds) :")
    for depth, obj_type, name in rows:
        indent = "  " * depth
        print(f"  {indent}[{obj_type}] {name}")
    print(f"  Temps : {elapsed:.1f} ms")
    print("  Neo4j fera ça en 1 ligne : MATCH (n)-[:EST_SOUS_TYPE_DE*]->(root {name:'Tronçon'})")

# =============================================================================
# EXERCICE 2 — Requêtes POI par rôle
# =============================================================================

def ex2_poi_by_role(conn, role):
    print_section(f"EXERCICE 2 — POIs pour le rôle {role.upper()}")

    sql = ROLE_QUERIES[role]
    t0 = time.time()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                DROP TABLE IF EXISTS mission_pois CASCADE;
                CREATE TABLE mission_pois (
                    id SERIAL PRIMARY KEY,
                    role TEXT,
                    source TEXT,
                    cleabs TEXT,
                    categorie TEXT,
                    nature TEXT,
                    nom TEXT,
                    geom GEOMETRY(Geometry, 2154)
                );
                INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
                SELECT '{role}', source, cleabs, categorie, nature, toponyme, geom
                FROM ({sql}) AS poi;
                SELECT COUNT(*) FROM mission_pois;
            """)
            total = cur.fetchone()[0]

            # Résumé par source
            cur.execute("SELECT source, COUNT(*) FROM mission_pois GROUP BY source ORDER BY count DESC;")
            breakdown = cur.fetchall()
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e}")
        return

    elapsed = (time.time() - t0) * 1000
    print(f"  Total POIs identifiés : {total} ({elapsed:.1f} ms)")
    print(f"\n  {'Source':<20} | {'Count':>5}")
    print(f"  {'-'*30}")
    for source, count in breakdown:
        print(f"  {source:<20} | {count:>5}")

    print(f"\n  Table mission_pois prête pour la phase 2.")

# =============================================================================
# EXERCICE 3 — Clustering spatial (ST_ClusterDBSCAN)
# =============================================================================

def ex3_clustering(conn):
    print_section("EXERCICE 3 — Clustering spatial (ST_ClusterDBSCAN)")

    query = """
        WITH clustered AS (
            SELECT *,
                   ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cluster_id
            FROM mission_pois
        )
        SELECT cluster_id, COUNT(*) AS nb_pois, role
        FROM clustered
        WHERE cluster_id IS NOT NULL
        GROUP BY cluster_id, role
        ORDER BY nb_pois DESC
        LIMIT 10;
    """
    t0 = time.time()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        elapsed = (time.time() - t0) * 1000

        if not rows:
            print("  Aucun cluster détecté (réduisez eps ou les POIs sont trop dispersés).")
        else:
            print(f"  Top 10 grappes tactiques (rayon 2km) :")
            print(f"  {'Cluster':>8} | {'POIs':>5} | {'Rôle'}")
            print(f"  {'-'*30}")
            for cid, count, role in rows:
                print(f"  {cid:>8} | {count:>5} | {role}")
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e} — ST_ClusterDBSCAN requiert PostGIS >= 2.4")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=ROLES, required=True,
                        help="Rôle de l'agent (attaque/defense/ravitaillement/energie)")
    args = parser.parse_args()

    print(f"""
  ============================================================
   OPÉRATION MANTICORE — Phase 1 : Reconnaissance
   Rôle : {args.role.upper()}
  ============================================================
    """)
    conn = get_conn()
    try:
        ex1_ontologie_recursive(conn)
        ex2_poi_by_role(conn, args.role)
        ex3_clustering(conn)
    finally:
        conn.close()
