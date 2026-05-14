WITH cc AS (
    SELECT node, component FROM pgr_connectedComponents(
        'SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost > 0'
    )
), main_comp AS (
    SELECT component FROM cc GROUP BY component ORDER BY count(*) DESC LIMIT 1
)
SELECT p.role, p.nom, p.source
FROM mission_pois p
JOIN LATERAL (SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1) v ON TRUE
JOIN cc ON cc.node = v.id
WHERE cc.component NOT IN (SELECT component FROM main_comp)
ORDER BY p.role, p.nom;
