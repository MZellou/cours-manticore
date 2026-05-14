SELECT p.nom AS cible, p.nature,
       avg(r.vitesse_moyenne_vl) AS vitesse_moy_kmh
FROM mission_pois p
JOIN troncon_de_route r ON ST_DWithin(p.geom, r.geometrie, 2000)
WHERE p.role = 'attaque'
GROUP BY p.nom, p.nature
ORDER BY vitesse_moy_kmh;
