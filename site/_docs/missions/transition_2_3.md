---
title: Transition 2 → 3
parent: Missions
nav_order: 7
layout: default
---

# Transition Phase 2 → Phase 3

> Pause synthèse avant la simulation. **5 minutes de lecture.**

---

## Ce que vous avez appris en Phase 2

| Compétence | Pourquoi c'est crucial Phase 3 |
|-----------|-------------------------------|
| Construction d'un graphe (`ways`, `ways_vertices_pgr`) | Vous allez **simuler des coupes** sur ces arêtes |
| `pgr_dijkstra`, routage contraint | Vous allez **mesurer l'impact** d'une coupe sur les chemins |
| Migration vers Neo4j (`MERGE`) | Vous allez **exploiter APOC** sur le même graphe |
| `OPTIONAL MATCH`, patterns Cypher | Indispensable pour la T2 (chemins entre rôles) |
| Snap des POIs aux sommets | Toutes les analyses Phase 3 partent de ces snaps |

---

## Ce qui change en Phase 3

### De la **construction** à l'**analyse**

Phase 2 : on a *construit* le graphe et fait les premières requêtes.
Phase 3 : on l'**attaque** et on **mesure** sa résilience.

### Trois nouvelles familles d'outils

#### 1. **APOC** (algorithmes Cypher)

Jusqu'ici on faisait `MATCH … RETURN`. Phase 3, on appelle des **procédures** :

```cypher
CALL apoc.algo.betweenness(['POI'], ['DISTANCE'], 'BOTH') YIELD node, score …
CALL apoc.path.subgraphAll(start, {maxLevel: 2}) …
```

→ Lecture : [APOC]({% link _docs/theorie/avance/apoc.md %}) (5 min, **essentiel**)

#### 2. **Lecture de plans** (`EXPLAIN ANALYZE` / `PROFILE`)

Phase 3 vous demande de **mesurer** SQL vs Cypher. Vous devez savoir lire un plan :

- `Seq Scan` (mauvais) vs `Index Scan` (bon)
- `AllNodesScan` (catastrophique) vs `NodeIndexSeek` (bon)

→ Lecture : [SQL — limites & EXPLAIN]({% link _docs/theorie/avance/sql_recursion.md %}) (5 min)

#### 3. **Simulation destructive**

Vous allez **modifier `ways`** (mettre `cost = -1` sur des arêtes), mesurer, puis **restaurer** depuis le backup.

> ⚠️ **Toujours** : `CREATE TABLE ways_backup AS SELECT * FROM ways;` avant de toucher `ways`.

---

## La démarche Phase 3 en une phrase

> *Identifier les choke points → couper → mesurer la dégradation → comparer SQL vs Cypher → cartographier.*

| Tâche | Méthode | Résultat |
|-------|---------|----------|
| T1 | Betweenness centrality (Cypher + APOC) | Top 5 nœuds critiques |
| T3 | Benchmark `EXPLAIN ANALYZE` / `PROFILE` | Tableau temps + LOC |
| T5–T8 | Coupes itératives + Dijkstra | Distance avant/après |
| T9 | `pgr_connectedComponents` | Nombre de composantes |
| T11 | Carte PNG | Synthèse visuelle |

---

## Avant de cliquer "Phase 3"

- [ ] [Checkpoint Phase 2]({% link _docs/missions/checkpoint_phase_2.md %}) passé
- [ ] [APOC]({% link _docs/theorie/avance/apoc.md %}) lu
- [ ] [SQL — limites & EXPLAIN]({% link _docs/theorie/avance/sql_recursion.md %}) lu
- [ ] Backup `ways` prêt à être créé : `CREATE TABLE ways_backup AS SELECT * FROM ways;`

---

{% include nav_phase.html prev_url="/missions/checkpoint_phase_2/" prev_label="Checkpoint Phase 2" next_url="/missions/phase_3_simulation/" next_label="Phase 3 — Simulation" %}
