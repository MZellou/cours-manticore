MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*1..3]-(e:POI {role: 'energie'})-[:DISTANCE*1..3]-(d:POI {role: 'defense'})
RETURN
    [n IN nodes(path) | n.nom] AS etapes,
    length(path) AS sauts,
    reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
