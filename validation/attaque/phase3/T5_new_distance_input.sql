SELECT agg_cost AS nouvelle_distance
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    49416, 17891, directed := false
) ORDER BY seq DESC LIMIT 1;
