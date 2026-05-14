SELECT p.toponyme AS port, z.toponyme AS caserne,
       ST_Distance(p.geometrie, z.geometrie) AS dist_m
FROM equipement_de_transport p
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(p.geometrie, z.geometrie, 5000)
WHERE p.nature = 'Port'
  AND z.nature IN ('Gendarmerie', 'Caserne')
ORDER BY dist_m;
