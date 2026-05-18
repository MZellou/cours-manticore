MATCH (p:POI {role: 'logistique'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;
