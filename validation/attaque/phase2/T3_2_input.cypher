MATCH (p:POI {role: 'attaque'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;
