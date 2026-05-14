SELECT source, count(*) AS nb FROM mission_pois WHERE role = 'ravitaillement' GROUP BY source ORDER BY nb DESC;
