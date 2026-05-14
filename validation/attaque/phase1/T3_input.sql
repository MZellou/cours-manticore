SELECT role, source, categorie, count(*)
FROM mission_pois
WHERE role = 'attaque'
GROUP BY role, source, categorie
ORDER BY role, source, categorie;
