SELECT 'normal' AS mode, max(agg_cost) AS total_cost
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1),
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'defense' LIMIT 1),
    directed := false
);
