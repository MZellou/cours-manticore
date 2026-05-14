MATCH path = (d:ClasseOntologie)-[:EST_SOUS_TYPE_DE*]->(o:ClasseOntologie {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy LIMIT 5;
