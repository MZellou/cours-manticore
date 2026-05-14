MATCH (p:POI) RETURN p.role, count(*) ORDER BY count DESC;
