MATCH (p:POI {role: 'attaque'})-[d:DISTANCE]->(q) RETURN p.nom, q.nom, d.meters ORDER BY d.meters LIMIT 10;
