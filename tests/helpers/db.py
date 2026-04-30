"""Shared test utilities: exec helpers, template detection, fixture resolution."""

from __future__ import annotations

import os
import re

import psycopg2
from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PG_DSN = {
    "host": os.getenv("POSTGIS_HOST", "localhost"),
    "port": int(os.getenv("POSTGIS_PORT", 5432)),
    "dbname": os.getenv("POSTGIS_DB", "bdtopo_manticore"),
    "user": os.getenv("POSTGIS_USER", "postgres"),
    "password": os.getenv("POSTGIS_PASSWORD", "manticore2026"),
}

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "manticore2026")

# ---------------------------------------------------------------------------
# Query classification
# ---------------------------------------------------------------------------

_WRITE_KEYWORDS = re.compile(
    r"^\s*(CREATE|DROP|INSERT|UPDATE|DELETE|ALTER)\b",
    re.IGNORECASE | re.MULTILINE,
)


def is_write_query(code: str) -> bool:
    """True if the SQL query mutates data (no rows returned)."""
    clean = re.sub(r"--.*$", "", code, flags=re.MULTILINE)
    return bool(_WRITE_KEYWORDS.search(clean))


def is_template(code: str) -> bool:
    """True if the query contains unresolved placeholders."""
    from tests.helpers.qmd_parser import is_template as _is_tpl
    return _is_tpl(code)


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------

def resolve_templates(code: str, **kwargs) -> str:
    """Replace known placeholders with runtime values."""
    if "src_vertex" in kwargs and "tgt_vertex" in kwargs:
        code = re.sub(r"\bsource_vertex\b", str(kwargs["src_vertex"]), code)
        code = re.sub(r"\btarget_vertex\b", str(kwargs["tgt_vertex"]), code)
        code = re.sub(r"\bsrc,\s*tgt\b", f"{kwargs['src_vertex']}, {kwargs['tgt_vertex']}", code)
        code = re.sub(r"\bsrc_vertex\b", str(kwargs["src_vertex"]), code)
        code = re.sub(r"\btgt_vertex\b", str(kwargs["tgt_vertex"]), code)

    if "edge_id" in kwargs:
        eid = kwargs["edge_id"]
        code = re.sub(r"<edge_id>", str(eid), code)
        code = re.sub(r"<edge1>,\s*<edge2>,\s*<edge3>",
                       f"{eid}, {eid+1}, {eid+2}", code)

    code = re.sub(r"\bvotre_table\b", "zone_d_activite_ou_d_interet", code)
    code = re.sub(r"\bvos_filtres\b", "categorie = 'Santé'", code)
    code = re.sub(r"\bvotre_role\b", "attaque", code)
    code = re.sub(r"<attaquées>", "(SELECT id FROM ways LIMIT 3)", code)
    code = re.sub(r"<protégées>", "(SELECT id FROM ways LIMIT 1)", code)

    return code


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------

def exec_sql(conn, query: str) -> list[tuple]:
    """Execute SQL, return rows. Raises on error."""
    with conn.cursor() as cur:
        cur.execute(query)
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            return []


def exec_cypher(driver, query: str, params: dict | None = None) -> list[dict]:
    """Execute Cypher, return records as dicts."""
    with driver.session() as session:
        result = session.run(query, parameters=params or {})
        return [dict(record) for record in result]
