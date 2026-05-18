SELECT source, count(*) AS nb FROM mission_pois WHERE role = 'attaque' GROUP BY source ORDER BY nb DESC;
