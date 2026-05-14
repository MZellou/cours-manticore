EXPLAIN (ANALYZE)
SELECT count(*) FROM mission_pois p
WHERE EXISTS (
    SELECT 1 FROM troncon_de_route r
    WHERE ST_DWithin(p.geom, r.geometrie, 500)
);
