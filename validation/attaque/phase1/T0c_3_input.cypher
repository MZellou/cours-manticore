MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC
