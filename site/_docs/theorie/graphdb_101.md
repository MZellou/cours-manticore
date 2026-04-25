---
layout: default
title: GraphDB 101
parent: Théorie
nav_order: 6
---

# GraphDB 101 : le modèle graphe en bases de données

> Les bases de données graphe stockent les **relations** comme des citoyens de première classe, pas comme des clés étrangères.

---

## Le modèle LPG (Labeled Property Graph)

Neo4j utilise le modèle **Labeled Property Graph** :

```
  ┌──────────────────┐         ┌──────────────────┐
  │  (:POI)           │         │  (:POI)           │
  │  labels: [POI]    │         │  labels: [POI]    │
  │  properties:      │         │  properties:      │
  │    nom: "Brest"   │──5400m──│    nom: "Quimper" │
  │    role: "attaque"│         │    role: "défense"│
  └──────────────────┘         └──────────────────┘
         │
         │ EST_SOUS_TYPE_DE
         ▼
  ┌──────────────────┐
  │  (:ClasseOntologie)│
  │  labels: [Detail]  │
  │  properties:       │
  │    name: "Aérodrome"│
  └──────────────────┘
```

**3 concepts** :

| Concept | Description | Exemple Cypher |
|---------|-------------|---------------|
| **Nœud** | Entité avec labels + propriétés | `(:POI {nom: "Brest"})` |
| **Relation** | Arête typée, directionnelle, avec propriétés | `[:DISTANCE {meters: 5400}]` |
| **Label** | "Classe" d'un nœud (filtre) | `:POI`, `:ClasseOntologie`, `:Detail` |

---

## Index-Free Adjacency

La différence fondamentale avec SQL :

**SQL** : pour trouver les voisins d'un nœud, on cherche dans un **index** (O(log n)).
**Neo4j** : chaque nœud stocke directement les **pointeurs** vers ses voisins (O(1)).

```
SQL :  SELECT * FROM edges WHERE source_id = 42;  → index lookup
Neo4j : MATCH (n)-[r]->(m) WHERE id(n) = 42      → pointeur direct
```

**Conséquence** : la traversée de graphe ne ralentit pas avec la taille de la base. Seul le **degré** du nœud compte.

---

## Cypher : le SQL du graphe

### Patterns de base

```cypher
-- Trouver tous les POIs d'attaque
MATCH (p:POI {role: 'attaque'}) RETURN p.nom, p.source;

-- Trouver les POIs connectés à un aérodrome
MATCH (a:POI {source: 'aerodrome'})-[r:DISTANCE]-(b:POI)
RETURN a.nom, b.nom, r.meters
ORDER BY r.meters LIMIT 10;

-- Traversée ontologique : tous les sous-types de "Tronçon de route"
MATCH path = (d)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy;
```

### Comparaison Cypher vs SQL

| Tâche | SQL | Cypher |
|------|-----|--------|
| Enfants d'un parent | `JOIN ... ON child.parent_id = parent.id` | `(c)-[:CHILD_OF]->(p)` |
| Tous les descendants | `WITH RECURSIVE ...` (10+ lignes) | `(c)-[:CHILD_OF*]->(p)` (1 pattern) |
| Plus court chemin | `pgr_dijkstra(...)` (fonction) | `shortestPath((a)-[*]-(b))` (pattern) |
| Tous les chemins A→B | Impossible nativement | `MATCH path = (a)-[*]-(b)` |
| Chemins via un nœud | 2 appels Dijkstra + collage | 2 patterns `MATCH` dans même requête |

---

## APOC : algorithmes de graphe

Neo4j + APOC ajoute des algorithmes natifs :

```cypher
-- Betweenness centrality : quels POIs sont les plus "stratégiques" ?
CALL apoc.algo.betweenness('POI', 'DISTANCE', 'meters') YIELD nodeId, score
MATCH (p:POI) WHERE id(p) = nodeId
RETURN p.nom, p.role, score ORDER BY score DESC LIMIT 10;

-- Sous-graphe accessible en N sauts
CALL apoc.path.subgraphAll(node, {maxLevel: 3, relationshipFilter: 'DISTANCE'});

-- Dijkstra avec poids
CALL apoc.algo.dijkstra(startNode, endNode, 'DISTANCE', 'meters') YIELD path, weight;
```

> **SQL équivalent** : la betweenness centrality nécessite un script Python qui exécute N×M requêtes Dijkstra. En Cypher, c'est 1 appel APOC.

---

## Quand le graphe perd contre SQL

Neo4j n'est **pas** bon pour :

| Tâche | Pourquoi |
|-------|----------|
| Jointures spatiales | Pas de `ST_Intersects` natif → pré-calculer les distances |
| Agrégations massives | `GROUP BY` + `HAVING` est plus mature en SQL |
| Full-text search | Utiliser Elasticsearch ou PostgreSQL FTS |
| Données tabulaires plates | Pas de gain vs SQL pour des simples filtres |

**Dans ce TD** : on utilise **les deux**. PostGIS pour le spatial, Neo4j pour l'ontologie et les traversées de réseau.

---

## Pour aller plus loin

- [NoSQL vs SQL]({% link _docs/theorie/nosql_vs_sql.md %}) — panorama des familles NoSQL
- [Phase 3 — Benchmark]({% link _docs/missions/phase_3_simulation.md %}) — mesurer SQL vs Cypher sur vos données
