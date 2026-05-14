SELECT categorie, count(*) AS nb FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') GROUP BY categorie ORDER BY nb DESC;
