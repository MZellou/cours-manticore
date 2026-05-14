PROFILE MATCH path = (d)-[:EST_SOUS_TYPE_DE*]->(o {name: 'Tronçon de route'})
RETURN count(path);
