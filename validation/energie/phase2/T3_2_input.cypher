MATCH (p:POI {role: 'energie'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;
