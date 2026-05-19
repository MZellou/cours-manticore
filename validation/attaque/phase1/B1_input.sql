SELECT nature, count(*) FROM construction_ponctuelle WHERE nature IN ('Antenne', 'Eolienne', 'Phare', 'Autre construction élevée') GROUP BY nature ORDER BY count DESC;
