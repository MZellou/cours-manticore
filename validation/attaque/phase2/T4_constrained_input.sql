SELECT 'constrained_attaque' AS mode, max(agg_cost) AS total_cost
FROM pgr_dijkstra(
    'SELECT id, source, target,
            CASE WHEN nature IN (''Chemin'',''Sentier'') THEN cost*0.7 ELSE cost*1.3 END AS cost,
            CASE WHEN nature IN (''Chemin'',''Sentier'') THEN reverse_cost*0.7 ELSE reverse_cost*1.3 END AS reverse_cost
     FROM ways',
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1),
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'defense' LIMIT 1),
    directed := false
);
