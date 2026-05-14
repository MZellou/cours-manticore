WITH start_vertex AS (
    SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1
),
reachable AS (
    SELECT node, agg_cost
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM ways',
        (SELECT id FROM start_vertex),
        (SELECT array_agg(id) FROM ways_vertices_pgr),
        directed := false
    )
    WHERE agg_cost <= 600
)
SELECT ST_ConvexHull(ST_Collect(v.geom)) AS isochrone_10min
FROM reachable r
JOIN ways_vertices_pgr v ON v.id = r.node;
