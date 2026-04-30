"""Test Phase 1 Cypher — parsed dynamically from corriges/phase_1.qmd."""

import pytest
from helpers.db import exec_cypher, is_template
from helpers.qmd_parser import extract_queries

QUERIES = extract_queries("corriges/phase_1.qmd", lang_filter=["cypher"])


@pytest.mark.needs_neo4j
@pytest.mark.parametrize("query", QUERIES, ids=lambda q: q.id)
def test_cypher(neo4j_ready, neo_driver, query):
    code = query.code
    if is_template(code):
        pytest.skip("template: unresolved placeholders")

    rows = exec_cypher(neo_driver, code)
    assert isinstance(rows, list), f"Cypher error ({query.section_header})"
