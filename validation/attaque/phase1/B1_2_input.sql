SELECT '5km' AS rayon, count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 5000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port'
UNION ALL
SELECT '10km', count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 10000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port'
UNION ALL
SELECT '20km', count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 20000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port';
