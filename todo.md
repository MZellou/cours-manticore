T0a : check le contenu de nature et nature_detaillee aussi 

duckdb -c "
  SELECT d.nature, d.cnt, o.short_def
  FROM (
    SELECT nature, count(*) as cnt
    FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet')
    WHERE categorie = 'Santé' GROUP BY nature
  ) d
  LEFT JOIN (
    SELECT name as obj_name, substring(definition, 1, 120) as short_def
    FROM read_parquet('data/ontologie/bdtopo_objects.parquet')
    WHERE parent_db_name = 'zone_d_activite_ou_d_interet'
  ) o ON d.nature = o.obj_name
  ORDER BY d.cnt DESC;"
┌───────────────────────────┬───────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│          nature           │  cnt  │                                                         short_def                                                          │
│          varchar          │ int64 │                                                          varchar                                                           │
├───────────────────────────┼───────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Maison de retraite        │  7842 │ #Informations:\n##Définition : Établissement d'hébergement pour personnes âgées, généralement médicalisé.\n##Regroupement  │
│ Hôpital                   │  2537 │ #Informations:\n##Définition : Établissement public ou privé, où sont effectués tous les soins médicaux et chirurgicaux,   │
│ Etablissement hospitalier │  2362 │ #Informations:\n##Définition : Autres établissements relevant de la loi hospitalière.\n##Regroupement : Etablissement hosp │
│ Etablissement thermal     │   134 │ #Informations:\n##Définition : Etablissement où l’on utilise les eaux médicinales à des fins thérapeutiques.\n##Regroupeme │
└───────────────────────────┴───────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

-> normalement tous les POI de la bdtopo sont dans l'ontologie. 