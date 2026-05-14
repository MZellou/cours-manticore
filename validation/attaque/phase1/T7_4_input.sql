SELECT z.toponyme AS zone, a.toponyme AS aero,
       ST_Distance(z.geometrie, a.geometrie) AS dist_m
FROM zone_d_activite_ou_d_interet z
JOIN aerodrome a
  ON ST_DWithin(z.geometrie, a.geometrie, 3000)
WHERE z.nature IN ('Zone industrielle', 'Zone d''activités')
  AND a.categorie IN ('Internationale', 'Nationale')
ORDER BY dist_m;
