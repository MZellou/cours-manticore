MATCH (a:POI {role: 'attaque'})-[d:DISTANCE]->(b:POI {role: 'attaque'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;
