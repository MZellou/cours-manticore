SELECT component, count(*) AS nb_sommets
FROM pgr_connectedComponents(
    'SELECT id, source, target, cost, reverse_cost FROM ways'
)
GROUP BY component ORDER BY nb_sommets DESC LIMIT 10;
