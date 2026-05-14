SELECT 1000 AS eps, count(DISTINCT cid) AS nb_clusters
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 1000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 2000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 3000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 5000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 5000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL;
