SELECT
    p.nom AS cible,
    p.nature,
    s.nature AS type_retenue,
    round(ST_Distance(p.geom, s.geometrie)::numeric, 0) AS distance_m
FROM mission_pois p
JOIN surface_hydrographique s
    ON ST_DWithin(p.geom, s.geometrie, 500)
WHERE p.role = 'attaque'
  AND s.nature IN ('Retenue', 'Retenue-barrage', 'Lac')
ORDER BY distance_m;
