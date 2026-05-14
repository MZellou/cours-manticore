MATCH (p:POI)
WITH p.role AS role, collect(p.nom) AS noms
UNWIND noms AS nom
RETURN role, nom ORDER BY role, nom;
