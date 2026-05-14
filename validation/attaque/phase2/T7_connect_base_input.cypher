MATCH (b:Base {nom: 'Point de ralliement Alpha'})
MATCH (p:POI)
WITH b, p, point({latitude: toFloat(split(b.coords, ', ')[0]),
                  longitude: toFloat(split(b.coords, ', ')[1])}) AS basePt,
     point({latitude: p.lat, longitude: p.lon}) AS poiPt
WITH b, p, point.distance(basePt, poiPt) AS dist
WHERE dist < 10000
MERGE (b)-[r:DISTANCE {meters: toInteger(dist)}]->(p)
RETURN count(r) AS relations_creees;
