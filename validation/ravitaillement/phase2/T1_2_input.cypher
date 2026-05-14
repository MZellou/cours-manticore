MATCH (p:POI) RETURN p.role AS role, count(p) AS nb ORDER BY role;
