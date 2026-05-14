SELECT nature, count(*) AS nb FROM zone_d_activite_ou_d_interet WHERE categorie = 'Santé' GROUP BY nature ORDER BY nb DESC;
