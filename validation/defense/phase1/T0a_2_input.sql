SELECT categorie, count(*) AS nb FROM zone_d_activite_ou_d_interet GROUP BY categorie HAVING count(*) > 10 ORDER BY nb DESC;
