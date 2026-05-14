MATCH (p:POI {role: 'ravitaillement'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;
