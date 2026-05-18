MATCH path = (child:ClasseOntologie)-[:EST_SOUS_TYPE_DE*1..3]->(root:ClasseOntologie {obj_type: 'Database'}) RETURN [n IN nodes(path) | n.name] AS names LIMIT 10;
