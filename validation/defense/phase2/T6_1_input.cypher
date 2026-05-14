MATCH (p:POI {role: 'defense'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;
