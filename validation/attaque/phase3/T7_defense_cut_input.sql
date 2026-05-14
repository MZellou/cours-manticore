-- Attack edges: [13429, 10666, 13434, 13433, 53508]
-- Defense edges: [13420, 10737, 15738, 54131, 54113]
-- Effective cuts (attacked but not protected): [13429, 10666, 13434, 13433, 53508]
UPDATE ways SET cost = -1, reverse_cost = -1
WHERE id IN (13429, 10666, 13434, 13433, 53508);
