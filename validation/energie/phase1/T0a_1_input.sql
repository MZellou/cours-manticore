SELECT categorie, count(*) AS nb FROM zone_d_activite_ou_d_interet GROUP BY categorie ORDER BY nb DESC;
