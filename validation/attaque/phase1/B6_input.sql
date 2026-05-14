SELECT
    ST_SnapToGrid(geom, 5000) AS carreau,
    count(*) AS nb_antennes
FROM mission_pois
WHERE role = 'attaque' AND source = 'communication'
GROUP BY ST_SnapToGrid(geom, 5000)
ORDER BY nb_antennes;
