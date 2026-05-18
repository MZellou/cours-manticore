MATCH (a:POI {role: 'attaque'})-[d:DISTANCE]->(b:POI) WHERE b.role <> 'attaque' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;
