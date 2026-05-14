MATCH (p:POI) WHERE EXISTS { (p)-[:DISTANCE*]-() }
RETURN count(p);
