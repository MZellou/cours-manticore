SELECT p.nom, p.role,
       v.id AS vertex_id,
       ST_Distance(p.geom, v.geom) AS distance_snap
FROM mission_pois p
CROSS JOIN LATERAL (
    SELECT id, geom FROM ways_vertices_pgr
    ORDER BY geom <-> p.geom LIMIT 1
) v
ORDER BY distance_snap DESC LIMIT 10;
