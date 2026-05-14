SELECT
    c.nature,
    c.toponyme AS nom_ouvrage,
    r.nature AS type_route,
    r.importance
FROM construction_lineaire c
JOIN troncon_de_route r
    ON ST_Intersects(c.geometrie, r.geometrie)
WHERE c.nature IN ('Pont', 'Tunnel')
  AND CAST(r.importance AS INTEGER) <= 2
ORDER BY c.nature, r.importance;
