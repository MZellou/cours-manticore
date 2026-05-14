MATCH (a:POI {role: 'defense'})-[d:DISTANCE]->(b:POI) WHERE b.role <> 'defense' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;
