WITH poi_vertices AS (
    SELECT p.nom, p.role,
           (SELECT v.id FROM ways_vertices_pgr v ORDER BY v.geom <-> p.geom LIMIT 1) AS vid
    FROM mission_pois p
    WHERE p.role = 'attaque'
)
SELECT start_vid, end_vid, agg_cost AS distance_m
FROM pgr_dijkstraCostMatrix(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    (SELECT array_agg(vid) FROM poi_vertices),
    directed := false
)
ORDER BY agg_cost DESC LIMIT 20;
