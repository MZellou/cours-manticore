"""Test Phase 3 Cypher (Neo4j) — parsed dynamically from corriges/phase_3.qmd."""

import pytest
from helpers.db import exec_cypher, is_template
from helpers.qmd_parser import extract_queries

QUERIES = extract_queries("corriges/phase_3.qmd", lang_filter=["cypher"])


@pytest.mark.needs_neo4j
@pytest.mark.parametrize("query", QUERIES, ids=lambda q: q.id)
def test_cypher(neo4j_ready, neo_driver, query):
    code = query.code
    if is_template(code):
        pytest.skip("template: unresolved placeholders")

    try:
        rows = exec_cypher(neo_driver, code)
        assert isinstance(rows, list), f"Cypher error ({query.section_header})"
    except Exception as e:
        if any(kw in str(e).lower() for kw in ["apoc", "gds", "unknown function"]):
            pytest.skip(f"Missing plugin: {e}")
        raise
