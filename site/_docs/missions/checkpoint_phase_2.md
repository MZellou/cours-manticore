---
title: Checkpoint Phase 2
parent: Missions
nav_order: 6
layout: default
---

# ✅ Checkpoint Phase 2 → Phase 3

> Sanity check : le graphe routier et le graphe Neo4j sont opérationnels avant la simulation.

---

## 1. Le graphe routier (PostGIS / pgRouting) est chargé

```sql
SELECT
  (SELECT count(*) FROM ways) AS nb_edges,
  (SELECT count(*) FROM ways_vertices_pgr) AS nb_vertices,
  (SELECT count(*) FROM troncon_de_route WHERE ST_Intersects(geom, (SELECT geom FROM epci LIMIT 1))) AS nb_troncons_epci;
```

| Symptôme | Diagnostic |
|----------|------------|
| `nb_edges` >> `nb_troncons_epci` (typiquement ×1.5 à ×3) | ✅ r2gg a découpé aux intersections, c'est normal |
| `nb_edges = 0` | ❌ Gold Dump pas chargé. Voir [setup]({% link _docs/setup.md %}). |
| `nb_edges = nb_troncons_epci` | ⚠️ Pas de découpage = graphe inutilisable, signaler à l'instructeur |

---

## 2. Tous les POIs ont un sommet snap

```sql
SELECT
  count(*) AS total,
  count(vertex_id) AS avec_snap,
  count(*) FILTER (WHERE vertex_id IS NULL) AS sans_snap
FROM mission_pois;
```

→ `sans_snap` doit être à 0. Sinon, relancez votre requête de snap (Phase 2 T2).

### Distribution des distances de snap

```sql
SELECT
  percentile_cont(0.5) WITHIN GROUP (ORDER BY dist_snap) AS p50,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY dist_snap) AS p95,
  max(dist_snap) AS max_m
FROM mission_pois
WHERE dist_snap IS NOT NULL;
```

| `p95` | Diagnostic |
|-------|------------|
| < 200 m | ✅ Excellent — tous les POIs sont sur le réseau |
| 200–1000 m | ✅ Acceptable — quelques POIs ruraux |
| > 1000 m | ⚠️ Beaucoup de POIs hors-réseau — pertinence du routage à discuter |

---

## 3. Dijkstra fonctionne entre 2 POIs

```sql
WITH pair AS (
  SELECT
    (SELECT vertex_id FROM mission_pois WHERE role = 'attaque'   AND vertex_id IS NOT NULL LIMIT 1) AS a,
    (SELECT vertex_id FROM mission_pois WHERE role = 'défense'   AND vertex_id IS NOT NULL LIMIT 1) AS d
)
SELECT count(*) AS nb_etapes, max(agg_cost) AS distance_totale
FROM pair, pgr_dijkstra(
  'SELECT id, source, target, cost, reverse_cost FROM ways',
  pair.a, pair.d, directed := false
);
```

→ `nb_etapes > 0` et `distance_totale > 0`. Si vide : le graphe est non connexe ou les sommets sont isolés.

---

## 4. Neo4j contient les POIs des 4 rôles

Dans Neo4j Browser :

```cypher
MATCH (p:POI)
RETURN p.role AS role, count(*) AS nb
ORDER BY role;
```

→ 4 lignes, chacune `nb > 0`. Si manquant, relancer `python scripts/02_migrate_to_neo4j.py`.

---

## 5. L'ontologie est dans Neo4j

```cypher
MATCH (n:ClasseOntologie) RETURN count(n) AS nb_classes;
MATCH ()-[r:EST_SOUS_TYPE_DE]->() RETURN count(r) AS nb_relations;
```

→ Les deux > 0. Sinon, la migration ontologie a échoué.

---

## 6. Les indexes Neo4j sont en place

```cypher
SHOW INDEXES;
```

→ Au moins un index sur `(:POI {cleabs})` ou `(:POI {role})`. Sinon, requêtes lentes en Phase 3 :

```cypher
CREATE INDEX poi_cleabs IF NOT EXISTS FOR (p:POI) ON (p.cleabs);
CREATE INDEX poi_role IF NOT EXISTS FOR (p:POI) ON (p.role);
```

---

## 7. APOC est chargé

```cypher
CALL apoc.help('apoc') YIELD name RETURN count(*) AS apoc_procedures;
```

→ `> 0`. Sinon, vérifiez `docker compose ps neo4j` et la conf `NEO4J_PLUGINS`.

---

## 8. Auto-validation

Vous devriez pouvoir **expliquer** sans LLM :

- Différence `cost` vs `reverse_cost` (et la convention `-1`)
- Pourquoi le snap d'un POI utilise `<->` et pas `ST_Distance`
- `MERGE` vs `CREATE` en Cypher
- Quand préférer pgRouting vs Cypher pour un parcours

---

{% include nav_phase.html prev_url="/missions/phase_2_cartographie/" prev_label="Phase 2" next_url="/missions/transition_2_3/" next_label="Transition 2→3" %}
