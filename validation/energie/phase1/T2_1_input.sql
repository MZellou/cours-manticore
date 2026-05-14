SELECT source, count(*) AS nb FROM mission_pois WHERE role = 'energie' GROUP BY source ORDER BY nb DESC;
