SELECT id, ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM ways_vertices_pgr LIMIT 10;
