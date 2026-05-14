MATCH (p:POI {role: 'energie'})-[d:DISTANCE]->() RETURN p.source AS src, count(d) AS nb_voisins, avg(d.meters) AS dist_moy ORDER BY nb_voisins DESC;
