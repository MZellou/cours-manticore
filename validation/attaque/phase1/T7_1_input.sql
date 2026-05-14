SELECT pt.importance, h.toponyme AS hopital,
       ST_Distance(pt.geometrie, h.geometrie) AS dist_m
FROM poste_de_transformation pt
JOIN zone_d_activite_ou_d_interet h
  ON ST_DWithin(pt.geometrie, h.geometrie, 1000)
WHERE CAST(pt.importance AS INTEGER) <= 3
  AND h.nature IN ('Hôpital', 'Établissement hospitalier');
