SELECT count(*) AS total, count(*) FILTER (WHERE nature = 'Chemin') AS chemins, count(*) FILTER (WHERE importance = '1' OR importance = '2' OR importance = '3') AS importance_haute FROM ways;
