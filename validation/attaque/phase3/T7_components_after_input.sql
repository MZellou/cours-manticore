SELECT count(DISTINCT component) AS nb_composantes
FROM pgr_connectedComponents(
    'SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost > 0'
);
