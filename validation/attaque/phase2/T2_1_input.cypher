MATCH (c:ClasseOntologie {name: 'Bâtiment'})<-[:EST_SOUS_TYPE_DE*1..6]-(child) RETURN child.name, child.obj_type LIMIT 20;
