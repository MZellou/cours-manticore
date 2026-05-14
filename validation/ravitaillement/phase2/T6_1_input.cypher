MATCH (p:POI {role: 'ravitaillement'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;
