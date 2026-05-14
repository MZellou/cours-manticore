SELECT a.toponyme AS aero, e.toponyme AS port,
       ST_Distance(a.geometrie, e.geometrie) AS dist_m
FROM aerodrome a
JOIN equipement_de_transport e
  ON ST_DWithin(a.geometrie, e.geometrie, 5000)
WHERE a.categorie IN ('Internationale', 'Nationale')
  AND e.nature = 'Port';
