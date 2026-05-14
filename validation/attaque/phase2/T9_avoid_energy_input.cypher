MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*1..4]-(d:POI {role: 'defense'})
WHERE ALL(n IN nodes(path) WHERE n.role IS NULL OR n.role <> 'energie')
RETURN [n IN nodes(path) | n.nom] AS etapes,
       reduce(t=0, r IN relationships(path) | t+r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
