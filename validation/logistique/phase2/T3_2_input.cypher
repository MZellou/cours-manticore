MATCH (p:POI {role: 'logistique'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;
