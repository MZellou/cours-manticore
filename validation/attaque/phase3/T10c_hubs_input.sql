MATCH (p:POI)-[:DISTANCE]-(n)
WITH p, count(n) AS degre
WITH p, degre, avg(degre) AS degre_moyen
WHERE degre > 2 * degre_moyen
RETURN p.nom, p.role, degre, degre_moyen
ORDER BY degre DESC;
