MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*1..2]-(d:POI {role: 'defense', nature: 'Hôpital'})
RETURN
    [n IN nodes(path) | n.nom] AS etapes,
    length(path) AS sauts,
    reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
