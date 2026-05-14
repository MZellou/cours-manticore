MATCH (a:POI {role: 'energie'})-[d:DISTANCE]->(b:POI {role: 'energie'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;
