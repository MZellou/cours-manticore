"""Pytest fixtures for Manticore test suite.

Pipeline: docker check → 00_setup Brest → gold_dumps → 01_explore (×4 roles) → 02_migrate
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

# Ensure tests/ is on sys.path so `helpers.*` imports work
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
import pytest
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TEST_EPCI = "242900314"  # Brest Métropole
ROLES = ["attaque", "defense", "ravitaillement", "energie"]

from helpers.db import PG_DSN, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# ---------------------------------------------------------------------------
# DB connection helpers (local to conftest)
# ---------------------------------------------------------------------------


def _pg_conn():
    return psycopg2.connect(**PG_DSN)


def _wait_for_pg(timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            conn = _pg_conn()
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError(f"PostGIS not ready after {timeout}s")


def _wait_for_neo4j(timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
            driver.close()
            return True
        except Exception:
            time.sleep(3)
    raise RuntimeError(f"Neo4j not ready after {timeout}s")


def _table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            (table_name,),
        )
        return cur.fetchone()[0]


def _table_rowcount(conn, table_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table_name}")
        return cur.fetchone()[0]


def _run_script(script_path: str, extra_args: list[str] | None = None):
    cmd = [sys.executable, script_path] + (extra_args or [])
    print(f"  [SETUP] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  STDOUT: {result.stdout[-2000:]}")
        print(f"  STDERR: {result.stderr[-2000:]}")
        raise RuntimeError(f"Script {script_path} failed (rc={result.returncode})")
    return result


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def pg_conn():
    """PostGIS connection (session-scoped, autocommit)."""
    _wait_for_pg()
    conn = _pg_conn()
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def neo_driver():
    """Neo4j driver (session-scoped)."""
    _wait_for_neo4j()
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def db_ready(pg_conn):
    """Load BDTOPO tables via 00_setup.py."""
    if _table_exists(pg_conn, "zone_d_activite_ou_d_interet") and \
       _table_rowcount(pg_conn, "zone_d_activite_ou_d_interet") > 0:
        print("  [SETUP] Tables already loaded, skipping 00_setup.")
    else:
        print("\n  [SETUP] Running 00_setup for Brest...")
        _run_script("scripts/00_setup.py", ["--epci", TEST_EPCI, "--skip-spatial-filter"])
    return True


@pytest.fixture(scope="session")
def mission_pois_ready(pg_conn, db_ready):
    """Run 01_explore_postgis.py for all 4 roles → fills mission_pois."""
    if _table_exists(pg_conn, "mission_pois") and _table_rowcount(pg_conn, "mission_pois") > 0:
        print("  [SETUP] mission_pois already populated.")
        return True

    print("\n  [SETUP] Populating mission_pois for all roles...")
    for role in ROLES:
        _run_script("scripts/01_explore_postgis.py", ["--role", role])

    count = _table_rowcount(pg_conn, "mission_pois")
    assert count > 0, "mission_pois empty after running all roles"
    print(f"  [SETUP] mission_pois: {count} rows")
    return True


@pytest.fixture(scope="session")
def neo4j_ready(pg_conn, neo_driver, mission_pois_ready):
    """Run 02_migrate_to_neo4j.py."""
    with neo_driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS cnt")
        cnt = result.single()["cnt"]
        if cnt > 10:
            print(f"  [SETUP] Neo4j already populated ({cnt} nodes).")
            return True

    print("\n  [SETUP] Running 02_migrate_to_neo4j...")
    _run_script("scripts/02_migrate_to_neo4j.py")
    return True


@pytest.fixture(scope="session")
def has_gold_dumps(pg_conn, db_ready):
    """Check if pgRouting tables exist."""
    return _table_exists(pg_conn, "ways") and _table_rowcount(pg_conn, "ways") > 0


# ---------------------------------------------------------------------------
# Runtime value fixtures (for template resolution)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def routing_vertices(pg_conn, has_gold_dumps):
    """A pair of vertex IDs from mission_pois snapped to routing graph."""
    if not has_gold_dumps:
        return {"src_vertex": 1, "tgt_vertex": 2}
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT min(vertex_id), max(vertex_id)
            FROM (
                SELECT (SELECT v.id FROM ways_vertices_pgr v
                        ORDER BY v.geom <-> p.geom LIMIT 1) AS vertex_id
                FROM mission_pois p WHERE p.geom IS NOT NULL LIMIT 10
            ) AS pv
        """)
        row = cur.fetchone()
        return {"src_vertex": row[0], "tgt_vertex": row[1]}


@pytest.fixture(scope="session")
def sample_edge_id(pg_conn, has_gold_dumps):
    """An edge ID from the routing graph."""
    if not has_gold_dumps:
        return {"edge_id": 1}
    with pg_conn.cursor() as cur:
        cur.execute("SELECT id FROM ways LIMIT 1")
        return {"edge_id": cur.fetchone()[0]}
