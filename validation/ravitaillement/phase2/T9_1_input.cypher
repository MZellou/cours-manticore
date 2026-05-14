MATCH path = (a:POI {role: 'ravitaillement'})-[:DISTANCE*1..3]-(b) RETURN [n IN nodes(path) | n.nom] AS etapes, length(path) AS sauts LIMIT 5;
