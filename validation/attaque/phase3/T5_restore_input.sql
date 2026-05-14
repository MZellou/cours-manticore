UPDATE ways SET cost = ways_backup.cost, reverse_cost = ways_backup.reverse_cost
FROM ways_backup WHERE ways.id = ways_backup.id;
