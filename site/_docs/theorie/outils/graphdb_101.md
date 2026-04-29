---
layout: default
title: GraphDB 101
parent: Outils
grand_parent: Théorie
nav_order: 3
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
  │ (:ClasseOntologie)│
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

**L'analogie** : vous cherchez les amis de Jean.

- **En SQL** : `SELECT * FROM utilisateurs JOIN amis ON ... WHERE id = 'Jean'` → le SGBD parcourt un **index B-tree** de 1 million d'entrées → O(log n).
- **En graphe** : Jean a un **pointeur direct** vers chacun de ses amis, stocké dans le nœud lui-même. Trouver ses amis = suivre ces pointeurs → O(1) par saut, **indépendamment de la taille du graphe**.

```
SQL     :  SELECT * FROM edges WHERE source_id = 42;  → index lookup O(log n)
Neo4j   :  MATCH (n)-[r]->(m) WHERE id(n) = 42;     → pointeur direct O(1)
```

**Conséquence** : la traversée de graphe ne ralentit pas avec la taille de la base. Seul le **degré** du nœud (nombre de voisins) compte.

**Sur BDTOPO (3 sauts)** :
- SQL : 3 `JOIN` sur 20 millions de tronçons → secondes
- Cypher : `(a)-[:DISTANCE*1..3]->(b)` → millisecondes, chaque saut = O(degré du nœud)

---

## Cypher : le SQL du graphe

### Patterns de base

```cypher
// Trouver tous les POIs d'attaque
MATCH (p:POI {role: 'attaque'}) RETURN p.nom, p.source;

// Trouver les POIs connectés à un aérodrome
MATCH (a:POI {source: 'aerodrome'})-[r:DISTANCE]-(b:POI)
RETURN a.nom, b.nom, r.meters
ORDER BY r.meters LIMIT 10;

// Traversée ontologique : tous les sous-types de "Tronçon de route"
MATCH path = (d)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy;
```

### Comparaison Cypher vs SQL — 3 niveaux de profondeur

**Trouver les POIs à ≤ 2 sauts d'un aérodrome :**

```sql
-- SQL : WITH RECURSIVE (3 JOINs = construction d'une table temporaire)
WITH RECURSIVE reach AS (
  SELECT id_to FROM edges WHERE id_from = 42
  UNION ALL
  SELECT e.id_to FROM edges e JOIN reach r ON e.id_from = r.id_to
)
SELECT * FROM pois WHERE id IN (SELECT id_to FROM reach);
```

```cypher
// Cypher : un pattern, exécuté nativement par le moteur de graphe
MATCH (aero:POI {nature: 'Aérodrome'})-[:DISTANCE*1..2]->(cible:POI)
RETURN cible.nom, cible.nature;
```

> Le `*1..2` dans Cypher correspond au `WITH RECURSIVE` en SQL. La différence : Cypher le fait en **O(arêtes traversées)** — le moteur de graphe suit directement les pointeurs. SQL doit dabord **construire une table temporaire** en mémoire, puis interroger.

| Tâche | SQL | Cypher |
|-------|-----|--------|
| Enfants d'un parent | `JOIN ... ON child.parent_id = parent.id` | `(c)-[:CHILD_OF]->(p)` |
| Tous les descendants | `WITH RECURSIVE ...` (10+ lignes) | `(c)-[:CHILD_OF*]->(p)` (1 pattern) |
| Plus court chemin | `pgr_dijkstra(...)` (fonction PG) | `shortestPath((a)-[*]-(b))` |
| Chemins à N sauts max | Requête récursive complexe | `(a)-[:REL*1..N]->(b)` |
| Traversal avec filtre | Multiple CTEs empilés | `MATCH ... WHERE` à chaque pattern |

---

## Algorithmes de graphe

> Pour les procédures APOC (Dijkstra, betweenness, subgraphAll…) et les détails GDS, voir [APOC]({% link _docs/theorie/avance/apoc.md %}).

Les principaux algorithmes disponibles dans Neo4j via APOC :

| Algorithme | Rôle | Exemple rapide |
|------------|------|---------------|
| `apoc.algo.dijkstra` | Plus court chemin pondéré | `apoc.algo.dijkstra(start, end, 'DISTANCE', 'meters')` |
| `apoc.path.subgraphAll` | Tous les nœuds dans un rayon | `apoc.path.subgraphAll(node, {maxLevel: 3})` |
| `gds.betweenness.stream()` | Centralité (APOC 5.x) | Mesure le score de betweenness sur un graphe projeté |
| `gds.pageRank.stream()` | PageRank | Popularité/rôle stratégique d'un nœud |

---

## Quand le graphe perd contre SQL

Neo4j n'est **pas** bon pour :

| Tâche | Pourquoi | Alternative |
|-------|----------|------------|
| Jointures spatiales | Pas de `ST_Intersects` natif | PostGIS |
| Agrégations massives | `GROUP BY` + `HAVING` plus mature en SQL | PostgreSQL |
| Full-text search | Pas de moteur FTS intégré | Elasticsearch ou PostgreSQL FTS |
| Données tabulaires plates | Pas de gain vs SQL pour des filtres simples | PostgreSQL |

**Dans ce TD** : PostGIS pour le spatial, pgRouting pour le routage SQL, Neo4j pour l'ontologie et les traversées de graphe. Chaque outil pour ce qu'il fait de mieux.

---

## Pour aller plus loin

- [NoSQL vs SQL]({% link _docs/theorie/fondements/01_pourquoi_ce_cours.md %}) — panorama des familles NoSQL et théorème CAP
- [pgRouting et r2gg]({% link _docs/theorie/outils/pgrouting_r2gg.md %}) — routage sur PostGIS
- [APOC]({% link _docs/theorie/avance/apoc.md %}) — procédures algorithmiques et GDS
