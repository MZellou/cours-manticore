SELECT source, count(*) AS nb FROM (
  SELECT 'aerodrome' AS source, cleabs, categorie, nature, toponyme AS nom, ST_Force2D(geometrie) AS geom
  FROM aerodrome WHERE categorie IN ('Internationale', 'Nationale')
  UNION ALL
  SELECT 'port', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature = 'Port' AND nature_detaillee = 'Port de commerce'
  UNION ALL
  SELECT 'zone_militaire', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE categorie = 'Administratif ou militaire' AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')
  UNION ALL
  SELECT 'tour_controle', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature = 'Tour de contrôle aérien'
  UNION ALL
  SELECT 'fragilite', cleabs, nature, nature_detaillee, NULL, ST_Force2D(geometrie)
  FROM construction_lineaire WHERE nature IN ('Pont', 'Tunnel')
  UNION ALL
  SELECT 'cible_symbolique', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE nature IN ('Préfecture', 'Police', 'Etablissement pénitentiaire', 'Administration centrale')
  UNION ALL
  SELECT 'infra_critique', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE nature IN ('Station d''épuration', 'Usine de production d''eau potable')
  UNION ALL
  SELECT 'noeud_transport', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature IN ('Gare voyageurs uniquement', 'Aire de repos ou de service', 'Péage')
  UNION ALL
  SELECT 'communication', cleabs, NULL::text, nature, toponyme, ST_Force2D(geometrie)
  FROM construction_ponctuelle WHERE nature = 'Antenne'
  UNION ALL
  SELECT 'retenue_eau', cleabs, nature, nature, NULL, ST_Force2D(geometrie)
  FROM surface_hydrographique WHERE nature IN ('Retenue', 'Retenue-barrage', 'Lac')
) AS poi GROUP BY source ORDER BY nb DESC;
