MATCH (a:POI {role: 'energie'})-[d:DISTANCE]->(b:POI) WHERE b.role <> 'energie' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;
