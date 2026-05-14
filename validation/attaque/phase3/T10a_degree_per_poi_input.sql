MATCH (p:POI)-[r:DISTANCE]-(neighbor)
RETURN p.nom, p.role, count(neighbor) AS degre
ORDER BY degre DESC LIMIT 10;
