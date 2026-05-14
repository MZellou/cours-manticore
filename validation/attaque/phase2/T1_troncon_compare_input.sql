SELECT
    (SELECT count(*) FROM ways) AS nb_arretes_ways,
    (SELECT count(*) FROM troncon_de_route) AS nb_troncons_bdtopo;
