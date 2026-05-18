SELECT nature, count(*) FROM construction_ponctuelle WHERE nature IN ('Tour', 'Antenne', 'Château d''eau', 'Éolienne') GROUP BY nature ORDER BY count DESC;
