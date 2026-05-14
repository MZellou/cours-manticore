SELECT p.nom, p.role,
       count(w.id) FILTER (WHERE w.cost > 0) AS edges_carrossables
FROM mission_pois p
CROSS JOIN LATERAL (
    SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
) v
LEFT JOIN ways w ON w.source = v.id OR w.target = v.id
GROUP BY p.id, p.nom, p.role
HAVING count(w.id) FILTER (WHERE w.cost > 0) = 0;
