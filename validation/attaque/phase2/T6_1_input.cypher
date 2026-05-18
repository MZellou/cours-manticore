MATCH (p:POI {role: 'attaque'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;
