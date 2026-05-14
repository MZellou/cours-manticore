WITH RECURSIVE hierarchy AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
    FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id
)
SELECT depth, obj_type, name FROM hierarchy ORDER BY depth;
