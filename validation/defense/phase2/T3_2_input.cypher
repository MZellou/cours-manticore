MATCH (p:POI {role: 'defense'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;
