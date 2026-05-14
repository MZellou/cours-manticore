MATCH (a:POI), (b:POI)
WHERE id(a) < id(b)
WITH a, b LIMIT 3
RETURN a.nom, b.nom, EXISTS { (a)-[:DISTANCE*1..3]-(b) } AS connectes;
