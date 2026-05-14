EXPLAIN (ANALYZE)
WITH RECURSIVE h AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT c.id, c.name, c.obj_type, c.parent_id, h.depth + 1
    FROM bdtopo_ontology c JOIN h ON c.parent_id = h.id
)
SELECT count(*) FROM h;
