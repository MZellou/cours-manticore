MATCH (a:POI {role: 'ravitaillement'})-[:DISTANCE]-(b:POI)-[:DISTANCE]-(c:POI)-[:DISTANCE]-(a) WHERE id(a) < id(b) AND id(b) < id(c) RETURN a.nom, b.nom, c.nom LIMIT 10;
