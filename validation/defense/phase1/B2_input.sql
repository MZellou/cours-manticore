SELECT count(*) FROM mission_pois p JOIN reservoir r ON ST_DWithin(p.geom, r.geometrie, 3000) WHERE p.role = 'defense' AND r.nature = 'Réservoir industriel';
