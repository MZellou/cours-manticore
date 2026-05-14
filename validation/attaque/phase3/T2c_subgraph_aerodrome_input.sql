MATCH (aero:POI {source: 'aerodrome'})
CALL apoc.path.subgraphAll(aero, {
    maxLevel: 2,
    relationshipFilter: 'DISTANCE',
    labelFilter: 'POI'
}) YIELD nodes, relationships
UNWIND nodes AS n
RETURN DISTINCT n.role, n.nom, n.source
ORDER BY n.role;
