MATCH (a:POI {role: 'defense'})-[d:DISTANCE]->(b:POI {role: 'defense'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;
