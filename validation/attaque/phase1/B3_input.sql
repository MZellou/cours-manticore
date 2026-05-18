SELECT count(*) FROM mission_pois p JOIN zone_d_activite_ou_d_interet z ON ST_DWithin(p.geom, z.geometrie, 5000) WHERE p.role = 'attaque' AND z.categorie = 'Enseignement';
