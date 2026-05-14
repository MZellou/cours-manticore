SELECT
    (SELECT count(*) FROM ways) AS nb_arretes,
    (SELECT count(*) FROM ways_vertices_pgr) AS nb_noeuds;
