MATCH (a:POI {role: 'ravitaillement'})-[d:DISTANCE]->(b:POI {role: 'ravitaillement'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;
