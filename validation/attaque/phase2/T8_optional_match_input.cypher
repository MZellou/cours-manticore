MATCH (p:POI)
OPTIONAL MATCH (p)-[r:DISTANCE]-(neighbor:POI)
RETURN p.nom, p.role, count(neighbor) AS nb_voisins
ORDER BY nb_voisins DESC;
