MATCH (p:POI {role: 'ravitaillement'}) RETURN p.nom, p.nature, p.source LIMIT 15;
