WITH clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid
    FROM mission_pois
)
SELECT cid, COUNT(*) AS nb FROM clustered WHERE cid IS NOT NULL GROUP BY cid ORDER BY nb DESC;
