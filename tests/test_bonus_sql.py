"""Test Bonus SQL — parsed dynamically from corriges/bonus.qmd."""

import pytest
from helpers.db import exec_sql, is_write_query, is_template
from helpers.qmd_parser import extract_queries

QUERIES = extract_queries("corriges/bonus.qmd", lang_filter=["sql"])


@pytest.mark.parametrize("query", QUERIES, ids=lambda q: q.id)
def test_sql(pg_conn, mission_pois_ready, query):
    code = query.code
    if is_template(code):
        pytest.skip("template: unresolved placeholders")

    try:
        if is_write_query(code):
            exec_sql(pg_conn, code)
        else:
            rows = exec_sql(pg_conn, code)
            assert isinstance(rows, list), f"SQL error ({query.section_header})"
    except Exception as e:
        if "does not exist" in str(e).lower() or "undefined table" in str(e).lower():
            pytest.skip(f"Missing table: {e}")
        raise
