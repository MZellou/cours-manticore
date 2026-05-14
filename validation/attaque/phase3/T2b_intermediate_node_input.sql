MATCH (a:POI {role: 'attaque'})
MATCH (e:POI {role: 'energie'})
MATCH (r:POI {role: 'ravitaillement'})
MATCH path = shortestPath((a)-[:DISTANCE*]-(r))
MATCH path2 = shortestPath((r)-[:DISTANCE*]-(e))
RETURN
    [n IN nodes(path) | n.nom] AS leg1,
    [n IN nodes(path2) | n.nom] AS leg2,
    reduce(t=0, rel IN relationships(path) | t+rel.meters)
    + reduce(t=0, rel IN relationships(path2) | t+rel.meters) AS total_m
ORDER BY total_m LIMIT 1;
