SELECT DISTINCT e.nature, e.nature_detaillee, z.nature AS zone_nature
FROM equipement_de_transport e
JOIN zone_d_activite_ou_d_interet z
  ON ST_Intersects(e.geometrie, z.geometrie)
WHERE z.nature = 'Zone industrielle'
LIMIT 20;
