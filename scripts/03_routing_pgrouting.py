"""
Phase 2/3 — Routage pgRouting : Dijkstra, Choke Points, Routage contraint
=========================================================================
Phase 2 : ex1 Dijkstra + ex3 routage contraint par rôle
Phase 3 : ex2 Choke Points (destruction d'arêtes + recalcul)

Usage : python scripts/03_routing_pgrouting.py --role ravitaillement
"""

import argparse
import os
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

ROLES = ["attaque", "defense", "ravitaillement", "energie"]

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
# EXERCICE 1 — Dijkstra entre 2 POIs
# =============================================================================

def ex1_dijkstra(conn):
    print_section("EXERCICE 1 — Itinéraire Dijkstra entre POIs")

    print("  Recherche du plus court chemin entre 2 POIs de mission_pois...\n")

    query = """
        WITH poi_vertices AS (
            SELECT p.id AS poi_id, p.nom,
                   (SELECT v.id FROM ways_vertices_pgr v
                    ORDER BY v.geom <-> p.geom LIMIT 1) AS vertex_id
            FROM mission_pois p
            WHERE p.geom IS NOT NULL
        ),
        start_poi AS (
            SELECT vertex_id FROM poi_vertices WHERE vertex_id IS NOT NULL LIMIT 1
        ),
        end_poi AS (
            SELECT vertex_id FROM poi_vertices WHERE vertex_id IS NOT NULL OFFSET 3 LIMIT 1
        )
        SELECT
            (SELECT vertex_id FROM start_poi) AS source,
            (SELECT vertex_id FROM end_poi) AS target;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            if not row or row[0] is None or row[1] is None:
                print("  [SKIP] Pas assez de POIs avec vertex pour le calcul.")
                return

            source, target = row
            t0 = time.time()
            cur.execute("""
                SELECT seq, node, edge, cost, agg_cost
                FROM pgr_dijkstra(
                    'SELECT id, source, target, cost, reverse_cost FROM ways',
                    %s, %s, directed := false
                );
            """, (source, target))
            path = cur.fetchall()
            elapsed = (time.time() - t0) * 1000

            if path:
                total_cost = path[-1][4] if path[-1][4] else 0
                print(f"  Source vertex : {source}, Target vertex : {target}")
                print(f"  Chemin : {len(path)} segments, coût total : {total_cost:.0f}")
                print(f"  Temps : {elapsed:.1f} ms")
            else:
                print("  Aucun chemin trouvé (POIs peut-être déconnectés).")
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e}")

# =============================================================================
# EXERCICE 2 — Choke Points (Phase 3)
# =============================================================================

def ex2_choke_points(conn):
    print_section("EXERCICE 2 — Choke Points (Simulation de destruction)")

    print("""
  Stratégie : identifier l'arête dont la suppression maximise l'allongement
  du chemin le plus court entre 2 POIs.
    """)

    query = """
        WITH poi_vertices AS (
            SELECT (SELECT v.id FROM ways_vertices_pgr v
                    ORDER BY v.geom <-> p.geom LIMIT 1) AS vertex_id
            FROM mission_pois p WHERE p.geom IS NOT NULL LIMIT 5
        ),
        bounds AS (
            SELECT min(vertex_id) AS src, max(vertex_id) AS tgt FROM poi_vertices
        ),
        -- Chemin original
        original AS (
            SELECT agg_cost AS original_cost
            FROM pgr_dijkstra(
                'SELECT id, source, target, cost, reverse_cost FROM ways',
                (SELECT src FROM bounds), (SELECT tgt FROM bounds), directed := false
            ) ORDER BY agg_cost DESC LIMIT 1
        ),
        -- Trouver les arêtes du chemin pour les supprimer une par une
        path_edges AS (
            SELECT edge FROM pgr_dijkstra(
                'SELECT id, source, target, cost, reverse_cost FROM ways',
                (SELECT src FROM bounds), (SELECT tgt FROM bounds), directed := false
            ) WHERE edge > 0
        )
        -- Supprimer chaque arête et recalculer
    """

    print("  [VIBE PROMPT] « Écris une requête pgRouting qui simule la destruction")
    print("   d'un pont en mettant cost=-1 sur un tronçon, puis recalcule le chemin. »\n")

    try:
        with conn.cursor() as cur:
            # 1. Trouver un chemin et ses arêtes
            cur.execute("""
                SELECT min(vertex_id) AS src, max(vertex_id) AS tgt
                FROM (
                    SELECT (SELECT v.id FROM ways_vertices_pgr v
                            ORDER BY v.geom <-> p.geom LIMIT 1) AS vertex_id
                    FROM mission_pois p WHERE p.geom IS NOT NULL LIMIT 5
                ) AS pv
            """)
            row = cur.fetchone()
            if not row or row[0] is None:
                print("  [SKIP] Pas de POIs pour le calcul.")
                return
            src, tgt = row

            # 2. Chemin original
            cur.execute("""
                SELECT max(agg_cost) FROM pgr_dijkstra(
                    'SELECT id, source, target, cost, reverse_cost FROM ways',
                    %s, %s, directed := false
                )
            """, (src, tgt))
            original_cost = cur.fetchone()[0] or 0

            # 3. Tester suppression de chaque arête du chemin (top 5)
            cur.execute("""
                SELECT edge FROM pgr_dijkstra(
                    'SELECT id, source, target, cost, reverse_cost FROM ways',
                    %s, %s, directed := false
                ) WHERE edge > 0
                LIMIT 5
            """, (src, tgt))
            edges = [r[0] for r in cur.fetchall()]

            print(f"  Chemin original : {original_cost:.0f} unités (src={src}, tgt={tgt})\n")
            print(f"  {'Edge supprimée':>15} | {'Nouveau coût':>12} | {'Delta':>8} | {'Allongement':>10}")
            print(f"  {'-'*55}")

            for edge_id in edges[:5]:
                cur.execute(f"""
                    SELECT max(agg_cost) FROM pgr_dijkstra(
                        'SELECT id, source, target, cost, reverse_cost FROM ways WHERE id != {edge_id}',
                        %s, %s, directed := false
                    )
                """, (src, tgt))
                new_cost = cur.fetchone()[0]
                if new_cost is None:
                    delta = "INJOIGNABLE"
                    print(f"  {edge_id:>15} | {'---':>12} | {'---':>8} | {delta:>10}")
                else:
                    pct = ((new_cost - original_cost) / original_cost * 100) if original_cost > 0 else 0
                    print(f"  {edge_id:>15} | {new_cost:>12.0f} | {new_cost-original_cost:>+8.0f} | {pct:>+9.1f}%")
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e}")

# =============================================================================
# EXERCICE 3 — Routage contraint par rôle
# =============================================================================

def ex3_constrained_routing(conn, role):
    print_section(f"EXERCICE 3 — Routage contraint (rôle {role.upper()})")

    constraints = {
        "ravitaillement": """
            -- Exclure les routes avec restrictions de poids pour poids lourds
            'SELECT id, source, target,
                    CASE WHEN restriction_de_poids_total IS NULL
                         THEN cost
                         ELSE -1  -- bloqué si restriction de poids
                    END AS cost,
                    CASE WHEN restriction_de_poids_total IS NULL
                         THEN reverse_cost
                         ELSE -1
                    END AS reverse_cost
             FROM ways'
        """,
        "energie": """
            -- Exclure les routes étroites (< 4m) pour convois exceptionnels
            'SELECT id, source, target,
                    CASE WHEN largeur_de_chaussee >= 4 OR largeur_de_chaussee IS NULL
                         THEN cost ELSE -1 END AS cost,
                    CASE WHEN largeur_de_chaussee >= 4 OR largeur_de_chaussee IS NULL
                         THEN reverse_cost ELSE -1 END AS reverse_cost
             FROM ways'
        """,
        "attaque": """
            -- Favoriser les routes secondaires (camouflage, évitement checkpoints)
            'SELECT id, source, target,
                    CASE WHEN nature IN (''Chemin'', ''Sentier'')
                         THEN cost * 0.7  -- bonus discrétion
                         ELSE cost * 1.3  -- pénalité grand axe
                    END AS cost,
                    reverse_cost * 1.1 AS reverse_cost
             FROM ways'
        """,
        "defense": """
            -- Prioriser les grands axes (rapidité de déploiement)
            'SELECT id, source, target,
                    CASE WHEN importance >= 3 OR nature = ''Autoroute''
                         THEN cost * 0.5
                         ELSE cost
                    END AS cost,
                    reverse_cost AS reverse_cost
             FROM ways'
        """,
    }

    constraint_sql = constraints.get(role, constraints["defense"])
    print(f"  Contrainte appliquée : {role}")
    print(f"  {constraint_sql[:80]}...\n")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT min(vertex_id), max(vertex_id)
                FROM (
                    SELECT (SELECT v.id FROM ways_vertices_pgr v
                            ORDER BY v.geom <-> p.geom LIMIT 1) AS vertex_id
                    FROM mission_pois p WHERE p.geom IS NOT NULL LIMIT 5
                ) AS pv
            """)
            row = cur.fetchone()
            if not row or row[0] is None:
                print("  [SKIP] Pas de POIs.")
                return
            src, tgt = row

            # Comparaison : normal vs contraint
            for label, sql in [("Normal", "SELECT id, source, target, cost, reverse_cost FROM ways"),
                               ("Contraint", constraint_sql)]:
                t0 = time.time()
                cur.execute(f"""
                    SELECT max(agg_cost) FROM pgr_dijkstra('{sql}', %s, %s, directed := false)
                """, (src, tgt))
                cost = cur.fetchone()[0]
                elapsed = (time.time() - t0) * 1000
                if cost:
                    print(f"  [{label:>10}] Coût : {cost:>10.0f} | {elapsed:.1f} ms")
                else:
                    print(f"  [{label:>10}] Aucun chemin trouvé")
    except psycopg2.Error as e:
        print(f"  [ERREUR] {e}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=ROLES, required=True)
    args = parser.parse_args()

    print(f"""
  ============================================================
   OPÉRATION MANTICORE — Phase 2/3 : Routage pgRouting
   Rôle : {args.role.upper()}
  ============================================================
    """)
    conn = get_conn()
    try:
        ex1_dijkstra(conn)
        ex3_constrained_routing(conn, args.role)
        ex2_choke_points(conn)
    finally:
        conn.close()
