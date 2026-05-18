MATCH (a:POI {role: 'logistique'})-[d:DISTANCE]->(b:POI) WHERE b.role <> 'logistique' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;
