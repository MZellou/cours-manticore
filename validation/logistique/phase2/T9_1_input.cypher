MATCH path = (a:POI {role: 'logistique'})-[:DISTANCE*1..3]-(b) RETURN [n IN nodes(path) | n.nom] AS etapes, length(path) AS sauts LIMIT 5;
