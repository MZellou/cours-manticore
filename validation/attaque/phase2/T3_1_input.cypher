MATCH (p:POI {role: 'attaque'}) RETURN p.nom, p.nature, p.source LIMIT 15;
