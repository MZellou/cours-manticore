SELECT nature, nature_detaillee, count(*) AS cnt FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') WHERE categorie = 'Santé' GROUP BY ALL ORDER BY cnt DESC;
