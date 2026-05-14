MATCH (p:POI)-[r:DISTANCE]-(neighbor)
RETURN p.role, count(neighbor) AS total_voisins, count(DISTINCT p) AS nb_pois
ORDER BY total_voisins DESC;
