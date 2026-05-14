SELECT
    count(*) FILTER (WHERE cost > 0) AS carrossables,
    count(*) FILTER (WHERE cost = -1) AS impassables,
    round(100.0 * count(*) FILTER (WHERE cost = -1) / count(*), 1) AS pct_impassables
FROM ways;
