MATCH (a:POI {role: 'logistique'})-[d:DISTANCE]->(b:POI {role: 'logistique'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;
