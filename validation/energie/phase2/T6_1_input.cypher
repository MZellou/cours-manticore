MATCH (p:POI {role: 'energie'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;
