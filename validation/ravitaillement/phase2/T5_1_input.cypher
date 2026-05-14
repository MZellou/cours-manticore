MATCH (p:POI {role: 'ravitaillement'})-[d:DISTANCE]->(q) WHERE d.meters < 1000 RETURN p.nom, q.nom, d.meters ORDER BY d.meters LIMIT 10;
