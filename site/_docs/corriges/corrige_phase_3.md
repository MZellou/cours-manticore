---
title: Corrigé Phase 3
parent: Corrigés
nav_order: 3
layout: default
---
# Corrigé Phase 3 — Simulation

> Solutions des exercices. Cliquer sur "Copier" pour récupérer le code.

---

## T1 — Choke Points

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**Approche SQL (pgRouting)** :

```sql
-- 1. Trouver un chemin de référence entre 2 POIs
SELECT edge FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    src, tgt, directed := false
) WHERE edge > 0;

-- 2. Boucle itérative (nécessite un script Python)
-- Pour chaque arête du chemin :
--   UPDATE ways SET cost = -1, reverse_cost = -1 WHERE id = <edge>;
--   Recalculer pgr_dijkstra → comparer distance
--   UPDATE ways SET cost = <original>, reverse_cost = <original> WHERE id = <edge>;
-- L'arête qui cause le plus grand détour = choke point
```

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**Approche Neo4j (betweenness centrality)** :

```cypher
CALL apoc.algo.betweenness('POI', 'DISTANCE', 'meters') YIELD nodeId, score
MATCH (p:POI) WHERE id(p) = nodeId
RETURN p.nom, p.role, score AS centralite
ORDER BY centralite DESC LIMIT 10;
```

Une seule requête — pas besoin de boucle Python.

---

## T2a — Tous les chemins entre deux rôles

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*]-(d:POI {role: 'defense', nature: 'Hôpital'})
RETURN
    [n IN nodes(path) | n.nom] AS etapes,
    length(path) AS sauts,
    reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
```

**Équivalent SQL** : CTE récursive ~30 lignes :

```sql
WITH RECURSIVE paths AS (
    SELECT source AS node, target AS next_node, meters AS cost,
           ARRAY[source, target] AS path_nodes, id AS edge_id
    FROM poi_distances WHERE source IN (SELECT id FROM poi WHERE role='attaque')
    UNION ALL
    SELECT p.next_node, d.target, p.cost + d.meters,
           p.path_nodes || d.target, d.id
    FROM paths p JOIN poi_distances d ON p.next_node = d.source
    WHERE d.target != ALL(p.path_nodes)  -- éviter les cycles
)
SELECT path_nodes, cost AS distance_m FROM paths
WHERE next_node IN (SELECT id FROM poi WHERE role='defense' AND nature='Hôpital')
ORDER BY cost LIMIT 5;
```

→ **Cypher gagne clairement** : 8 lignes vs 30+, et le SQL reste incomplet (pas de gestion propre des cycles).

---

## T2b — Plus court chemin avec nœud intermédiaire

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
MATCH (a:POI {role: 'attaque'})
MATCH (e:POI {role: 'energie'})
MATCH (r:POI {role: 'ravitaillement'})
MATCH path = shortestPath((a)-[:DISTANCE*]-(r))
MATCH path2 = shortestPath((r)-[:DISTANCE*]-(e))
RETURN
    [n IN nodes(path) | n.nom] AS leg1,
    [n IN nodes(path2) | n.nom] AS leg2,
    reduce(t=0, rel IN relationships(path) | t+rel.meters)
    + reduce(t=0, rel IN relationships(path2) | t+rel.meters) AS total_m
ORDER BY total_m LIMIT 1;
```

---

## T2c — Sous-graphe accessible depuis un POI

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
MATCH (aero:POI {source: 'aerodrome'})
CALL apoc.path.subgraphAll(aero, {
    maxLevel: 2,
    relationshipFilter: 'DISTANCE',
    labelFilter: 'POI'
}) YIELD nodes, relationships
UNWIND nodes AS n
RETURN DISTINCT n.role, n.nom, n.source
ORDER BY n.role;
```

---

## T3 — Requêtes benchmark

### Requête 1 — Traversée ontologique

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**SQL** :

```sql
EXPLAIN (ANALYZE)
WITH RECURSIVE h AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT c.id, c.name, c.obj_type, c.parent_id, h.depth + 1
    FROM bdtopo_ontology c JOIN h ON c.parent_id = h.id
)
SELECT count(*) FROM h;
```

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**Cypher** :

```cypher
PROFILE MATCH path = (d:Detail)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN count(path);
```

### Requête 4 — Spatial (SQL gagne)

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**SQL** :

```sql
EXPLAIN (ANALYZE)
SELECT count(*) FROM mission_pois p
WHERE EXISTS (
    SELECT 1 FROM troncon_de_route r
    WHERE ST_DWithin(p.geom, r.geometrie, 500)
);
```

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Pourquoi Cypher perd</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

Neo4j n'a pas d'index spatial natif sur les relations `DISTANCE`.
La requête "POIs à moins de 500m d'une route" nécessite un calcul de distance par paire :
pas scalable.

```cypher
// Approximation (ne filtre PAS sur 500m réels)
MATCH (p:POI) WHERE EXISTS { (p)-[:DISTANCE*]-() }
RETURN count(p);
```

→ **SQL gagne clairement** sur les opérations spatiales.

---

## T5 — Couper 1 arête

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
-- Sauvegarder
CREATE TABLE ways_backup AS SELECT * FROM ways;

-- Couper une arête
UPDATE ways SET cost = -1, reverse_cost = -1 WHERE id = <edge_id>;

-- Mesurer nouvelle distance
SELECT agg_cost AS nouvelle_distance
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    src_vertex, tgt_vertex, directed := false
) ORDER BY seq DESC LIMIT 1;

-- Restaurer
UPDATE ways SET cost = ways_backup.cost, reverse_cost = ways_backup.reverse_cost
FROM ways_backup WHERE ways.id = ways_backup.id;
```

**Équivalent Cypher** (vérification de connectivité) :

```cypher
MATCH (a:POI {role: 'attaque'})-[:DISTANCE*]-(b:POI {role: 'defense'})
RETURN EXISTS { (a)-[:DISTANCE*]-(b) } AS encore_connectes;
```

---

## T6 — Couper 3 arêtes

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
UPDATE ways SET cost = -1, reverse_cost = -1
WHERE id IN (<edge1>, <edge2>, <edge3>);
```

Pour documenter la dégradation, exécuter après chaque coupure :

```sql
-- Distance entre 2 POIs
SELECT agg_cost FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    src, tgt, directed := false
) ORDER BY seq DESC LIMIT 1;

-- POIs isolés (plus de chemin vers les autres)
SELECT count(DISTINCT component) AS composantes
FROM pgr_connectedComponents(
    'SELECT id, source, target, cost, reverse_cost FROM ways'
);
```

---

## T7 — Stratégie défensive

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
-- Restaurer tout
UPDATE ways SET cost = ways_backup.cost, reverse_cost = ways_backup.reverse_cost
FROM ways_backup WHERE ways.id = ways_backup.id;

-- Simuler la protection : les arêtes du défenseur ne peuvent pas être coupées
-- 1. L'attaquant choisit 5 arêtes à couper
-- 2. Le défenseur choisit 5 arêtes à protéger
-- 3. Si arête_attaquant = arête_défenseur → elle tient (pas coupée)

-- Résultat final : couper uniquement les arêtes attaquées ET non protégées
UPDATE ways SET cost = -1, reverse_cost = -1
WHERE id IN (<attaquées>) AND id NOT IN (<protégées>);
```

---

## T8 — Stratégie offensive

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
-- Pour chaque arête "importante" du chemin principal :
-- 1. Couper cette arête
-- 2. Mesurer la distance moyenne entre tous les POIs
-- 3. Restaurer
-- 4. Garder les 5 arêtes avec le plus gros impact

-- Impact = distance_moyenne_après - distance_moyenne_avant
```

Script Python pour automatiser :

```python
import psycopg2
conn = psycopg2.connect("...")
cur = conn.cursor()

# Distance de référence
cur.execute("SELECT avg(agg_cost) FROM ...")  # tous les chemins
ref = cur.fetchone()[0]

# Tester chaque arête du chemin
for edge_id in chemin_principal:
    cur.execute("UPDATE ways SET cost=-1, reverse_cost=-1 WHERE id=%s", (edge_id,))
    cur.execute("SELECT avg(agg_cost) FROM ...")  # recalculer
    new_dist = cur.fetchone()[0]
    impact = new_dist - ref
    print(f"Edge {edge_id}: impact = {impact:.0f}m")
    cur.execute("UPDATE ways SET cost=ways_backup.cost FROM ways_backup WHERE ways.id=%s", (edge_id,))
```

---

## T9 — Composantes connexes

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
SELECT component, count(*) AS nb_sommets
FROM pgr_connectedComponents(
    'SELECT id, source, target, cost, reverse_cost FROM ways'
)
GROUP BY component ORDER BY nb_sommets DESC LIMIT 5;
```

```cypher
// Vérifier la connexité du graphe POI
MATCH (a:POI), (b:POI)
WHERE id(a) < id(b)
RETURN EXISTS { (a)-[:DISTANCE*]-(b) } AS connectes,
       count(*) AS paires_testees;
```

---

## T10 — Centralité de degré

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
-- Degré de chaque POI
MATCH (p:POI)-[r:DISTANCE]-(neighbor)
RETURN p.nom, p.role, count(neighbor) AS degre
ORDER BY degre DESC LIMIT 10;

// Degré par rôle
MATCH (p:POI)-[r:DISTANCE]-(neighbor)
RETURN p.role, count(neighbor) AS total_voisins, count(DISTINCT p) AS nb_pois
ORDER BY total_voisins DESC;

// Hubs : degré > 2× la moyenne
MATCH (p:POI)-[:DISTANCE]-(n)
WITH p, count(n) AS degre, avg(count(n)) OVER () AS degre_moyen
WHERE degre > 2 * degre_moyen
RETURN p.nom, p.role, degre, degre_moyen
ORDER BY degre DESC;
```