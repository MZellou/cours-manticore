MATCH (p:POI)
WHERE NOT (p)-[:DISTANCE]-()
RETURN p.nom, p.role, p.source;
