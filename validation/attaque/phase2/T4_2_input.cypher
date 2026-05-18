MATCH (p:POI {role: 'attaque'})-[d:DISTANCE]->(q:POI) RETURN count(d) AS nb_relations, avg(d.meters) AS avg_dist, min(d.meters) AS min_dist, max(d.meters) AS max_dist;
