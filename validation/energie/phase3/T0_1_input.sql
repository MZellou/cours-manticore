SELECT count(*) AS total_edges, count(*) FILTER (WHERE cost IS NOT NULL) AS carrossable, count(*) FILTER (WHERE cost IS NULL) AS non_carrossable FROM ways;
