MATCH (d:ClasseOntologie)-[:EST_SOUS_TYPE_DE]->(o:ClasseOntologie {name: 'Tronçon de route'}) RETURN d.obj_type, d.name
