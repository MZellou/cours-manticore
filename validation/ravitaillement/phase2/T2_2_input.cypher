MATCH path = (root:ClasseOntologie {obj_type: 'Database'})-[:EST_SOUS_TYPE_DE*1..3]->(child) RETURN [n IN nodes(path) | n.name] AS names LIMIT 10;
