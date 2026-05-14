MATCH (p:POI {role: 'defense'}) RETURN p.nom, p.nature, p.source LIMIT 15;
