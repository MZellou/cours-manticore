MATCH (a:POI {role: 'ravitaillement'})-[d:DISTANCE]->(b:POI) WHERE b.role <> 'ravitaillement' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;
