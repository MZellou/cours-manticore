SELECT source, count(*) AS nb FROM mission_pois WHERE role = 'logistique' GROUP BY source ORDER BY nb DESC;
