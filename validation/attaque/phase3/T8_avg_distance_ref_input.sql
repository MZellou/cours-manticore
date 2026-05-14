-- Average distance from aerodrome (49416) to 3 defense hospitals (intact graph)
WITH d1 AS (
    SELECT agg_cost FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM ways',
        49416, 17891, directed := false
    ) ORDER BY seq DESC LIMIT 1
),
d2 AS (
    SELECT agg_cost FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM ways',
        49416, 23110, directed := false
    ) ORDER BY seq DESC LIMIT 1
),
d3 AS (
    SELECT agg_cost FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM ways',
        49416, 206, directed := false
    ) ORDER BY seq DESC LIMIT 1
)
SELECT round(avg(agg_cost)::numeric, 1) AS avg_distance_m
FROM (SELECT agg_cost FROM d1 UNION ALL SELECT agg_cost FROM d2 UNION ALL SELECT agg_cost FROM d3) sub;
