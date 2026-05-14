SELECT l.voltage, count(*) AS ponts_fragiles
FROM ligne_electrique l
JOIN construction_surfacique c
  ON ST_Intersects(l.geometrie, c.geometrie)
WHERE l.voltage IN ('400 kV', '225 kV')
  AND c.nature = 'Pont'
GROUP BY l.voltage;
