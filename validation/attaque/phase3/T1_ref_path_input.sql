SELECT edge, agg_cost
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    49416, 17891, directed := false
) WHERE edge > 0;
