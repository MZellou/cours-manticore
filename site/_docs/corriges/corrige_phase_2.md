---
title: Corrigé Phase 2
parent: Corrigés
nav_order: 2
layout: default
---
# Corrigé Phase 2 — Cartographie

> Solutions des exercices. Cliquer sur "Copier" pour récupérer le code.

---

## T1 — Explorer le graphe r2gg

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
-- Les arêtes
SELECT id, source, target, cost, reverse_cost, length_m
FROM ways LIMIT 10;

-- Les sommets
SELECT id, ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM ways_vertices_pgr LIMIT 10;

-- Comptage
SELECT
    (SELECT count(*) FROM ways) AS nb_arretes,
    (SELECT count(*) FROM ways_vertices_pgr) AS nb_noeuds;
```

**Pourquoi les counts diffèrent** : r2gg découpe les tronçons aux intersections → un tronçon long entre 2 intersections peut devenir N arêtes si d'autres routes le croisent.

---

## T2 — Associer les POIs aux sommets

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
SELECT p.nom, p.role,
       v.id AS vertex_id,
       ST_Distance(p.geom, v.geom) AS distance_snap
FROM mission_pois p
CROSS JOIN LATERAL (
    SELECT id, geom FROM ways_vertices_pgr
    ORDER BY geom <-> p.geom LIMIT 1
) v
ORDER BY distance_snap DESC LIMIT 10;
```

**POIs éloignés** : si `distance_snap` > 500m, le POI est hors du réseau routier (en mer, en montagne sans route). Le routage depuis ce POI sera imprécis.

---

## T3 — Calculer des itinéraires (Dijkstra)

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
SELECT seq, node, edge, cost, agg_cost
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1),
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'defense' LIMIT 1),
    directed := false
);
```

---

## T4 — Routage contraint par rôle

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**Ravitaillement** (poids lourds) :

```sql
SELECT max(agg_cost) FROM pgr_dijkstra(
    'SELECT id, source, target,
            CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE cost END AS cost,
            CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE reverse_cost END AS reverse_cost
     FROM ways',
    source_vertex, target_vertex, directed := false
);
```

**Rôle Énergie** (convois exceptionnels) :

```sql
-- Coût dynamique : routes étroites bloquées
CASE WHEN largeur_de_chaussee < 4 THEN -1 ELSE cost END
```

**Rôle Attaque** (discrétion) :

```sql
-- Favoriser les chemins, pénaliser les grands axes
CASE WHEN nature IN ('Chemin','Sentier') THEN cost*0.7 ELSE cost*1.3 END
```

**Rôle Défense** (rapidité) :

```sql
-- Priorité aux routes d'importance >= 3
CASE WHEN importance >= 3 THEN cost*0.5 ELSE cost END
```

---

## T5 — Migrer dans Neo4j

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```bash
python scripts/02_migrate_to_neo4j.py
```

```cypher
-- Vérifier les POIs chargés
MATCH (p:POI) RETURN p.role, count(*) ORDER BY count DESC;

-- Traversée ontologique
MATCH path = (d:Detail)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy LIMIT 5;

-- Chemin le plus court entre POIs
MATCH (a:POI), (b:POI) WHERE id(a) < id(b)
CALL apoc.algo.dijkstra(a, b, 'DISTANCE', 'meters')
YIELD path, weight
RETURN a.nom, b.nom, weight AS distance_m
ORDER BY weight DESC LIMIT 10
```

---

## T7 — Créer des nœuds personnalisés (CREATE / MERGE)

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
-- Créer une base avancée
CREATE (b:Base {
    nom: 'Point de ralliement Alpha',
    type: 'base_avancee',
    role: 'groupe',
    coords: '48.390, -4.486'
})
RETURN b;

-- Créer un point d'observation
CREATE (o:Base {
    nom: 'Observatoire hauteur 302',
    type: 'observation',
    role: 'defense'
})
RETURN o;

-- Connecter la base aux POIs proches (< 10km)
MATCH (b:Base {nom: 'Point de ralliement Alpha'})
MATCH (p:POI)
WITH b, p, point({latitude: toFloat(split(b.coords, ', ')[0]),
                  longitude: toFloat(split(b.coords, ', ')[1])}) AS basePt,
     point({latitude: ST_Y(p.geom), longitude: ST_X(p.geom)}) AS poiPt
WITH b, p, distance(basePt, poiPt) AS dist
WHERE dist < 10000
MERGE (b)-[r:DISTANCE {meters: toInteger(dist)}]->(p)
RETURN count(r) AS relations_creees;
```

---

## T8 — OPTIONAL MATCH et UNWIND

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```cypher
-- POIs sans connexion (isolés)
MATCH (p:POI)
WHERE NOT (p)-[:DISTANCE]-()
RETURN p.nom, p.role, p.source;

-- OPTIONAL MATCH : POIs avec leurs voisins
MATCH (p:POI)
OPTIONAL MATCH (p)-[r:DISTANCE]-(neighbor:POI)
RETURN p.nom, p.role, count(neighbor) AS nb_voisins
ORDER BY nb_voisins DESC;

-- UNWIND : lister les noms par rôle
MATCH (p:POI)
WITH p.role AS role, collect(p.nom) AS noms
UNWIND noms AS nom
RETURN role, nom ORDER BY role, nom;
```

**POIs isolés** : les POIs trop éloignés des routes n'ont pas été connectés par le script de migration. Ce sont des outliers spatiaux.

---

## T9 — Pattern matching avancé

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

**Chemins via énergie uniquement** :

```cypher
MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*]-(e:POI {role: 'energie'})-[:DISTANCE*]-(d:POI {role: 'defense'})
RETURN
    [n IN nodes(path) | n.nom] AS etapes,
    length(path) AS sauts,
    reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
```

**Triangles** :

```cypher
MATCH (a:POI)-[:DISTANCE]-(b:POI)-[:DISTANCE]-(c:POI)-[:DISTANCE]-(a)
WHERE id(a) < id(b) AND id(b) < id(c)
RETURN a.nom, b.nom, c.nom LIMIT 10;
```

**Défi — Chemin en évitant les POIs énergie** :

```cypher
MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*]-(d:POI {role: 'defense'})
WHERE ALL(n IN nodes(path) WHERE n.role IS NULL OR n.role <> 'energie')
RETURN [n IN nodes(path) | n.nom] AS etapes,
       reduce(t=0, r IN relationships(path) | t+r.meters) AS distance_m
ORDER BY distance_m LIMIT 5;
```

---

## T10 — Matrice de distances

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
WITH poi_vertices AS (
    SELECT p.nom, p.role,
           (SELECT v.id FROM ways_vertices_pgr v ORDER BY v.geom <-> p.geom LIMIT 1) AS vid
    FROM mission_pois p
    WHERE p.role = 'attaque'
)
SELECT source, target, agg_cost AS distance_m
FROM pgr_dijkstraCostMatrix(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    (SELECT array_agg(vid) FROM poi_vertices),
    directed := false
)
ORDER BY agg_cost DESC LIMIT 20;
```

---

## T11 — Isochrones

{: .solution-block}
<div class="solution-header">
  <span class="solution-label">Solution</span>
  <button class="copy-btn"><span class="copy-label">Copier</span></button>
</div>

```sql
WITH start_vertex AS (
    SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1
),
reachable AS (
    SELECT node, agg_cost
    FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM ways',
        (SELECT id FROM start_vertex),
        (SELECT array_agg(id) FROM ways_vertices_pgr),
        directed := false
    )
    WHERE agg_cost <= 600  -- 10 minutes
)
SELECT count(*) AS sommets_atteignables,
       min(agg_cost) AS min_sec,
       max(agg_cost) AS max_sec
FROM reachable;
```

**Bonus convex hull** (polygone isochrone) :

```sql
SELECT ST_ConvexHull(ST_Collect(v.geom)) AS isochrone_10min
FROM reachable r
JOIN ways_vertices_pgr v ON v.id = r.node;
```