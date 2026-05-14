MATCH (a:POI {role: 'attaque'}), (b:POI {role: 'defense'})
WHERE a.nom IS NOT NULL AND b.nom IS NOT NULL
WITH a, b LIMIT 1
CALL apoc.algo.dijkstra(a, b, 'DISTANCE', 'meters')
YIELD path, weight
RETURN a.nom, b.nom, weight AS distance_m
