SELECT a.toponyme AS aero, z.toponyme AS hopital,
       ST_Distance(a.geometrie, z.geometrie) AS distance_m
FROM aerodrome a
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(a.geometrie, z.geometrie, 2000)
WHERE z.nature IN ('Hôpital', 'Établissement hospitalier');
