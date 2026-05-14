MATCH (a:POI {nom: 'Aérodrome de Grenoble-le Versoud'})
MATCH (b:POI {role: 'defense', source: 'hopital'})
WITH a, b LIMIT 1
RETURN a.nom, b.nom, EXISTS { (a)-[:DISTANCE*]-(b) } AS connectes;
