WITH forces AS (
    SELECT ST_Force2D(geometrie) AS geom, nature, toponyme
    FROM zone_d_activite_ou_d_interet
    WHERE categorie = 'Administratif ou militaire'
      AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')
),
clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER () AS cid
    FROM forces
)
SELECT cid, count(*) AS nb_forces, string_agg(toponyme, ', ') AS sites
FROM clustered WHERE cid IS NOT NULL
GROUP BY cid ORDER BY nb_forces DESC;
