---
layout: default
title: Phase 3 — Simulation
parent: Missions
nav_order: 4
---

> *"Simuler une attaque sur le réseau et comparer les approches SQL vs Graphe."*

**Mode** : Groupe (les 4 rôles collaborent sur la simulation).
**Durée estimée** : 1h30

---

## Comprendre : quand Cypher est-il réellement supérieur à SQL ?

Avant de simuler, il faut comprendre **pourquoi** on utilise deux moteurs.
La réponse n'est pas "Cypher est toujours mieux" — c'est **chaque outil excelle sur des formes de requêtes différentes**.

### Rappel du modèle de données

```
Neo4j :                        PostGIS :
┌─────────────────────┐        ┌──────────────────────────┐
│ (:ClasseOntologie)  │        │ bdtopo_ontology          │
│   .name             │        │   id, name, obj_type,    │
│   .obj_type         │        │   parent_id              │
│                     │        ├──────────────────────────┤
│ -[:EST_SOUS_TYPE_DE]│        │ mission_pois             │
│                     │        │   role, source, nature,   │
│ (:POI)              │        │   nom, geom              │
│   .role, .source    │        ├──────────────────────────┤
│   .nature, .nom     │        │ ways / ways_vertices_pgr │
│                     │        │   source, target, cost   │
│ -[:DISTANCE {meters}]│       └──────────────────────────┘
└─────────────────────┘
```

---

## Tâches

### T1 — Choke Points : deux approches, deux mondes

Un choke point est un nœud ou une arête dont la suppression **maximise l'impact**
sur la connectivité du réseau.

#### Approche SQL (PostGIS + pgRouting)

```sql
-- 1. Trouver un chemin
SELECT edge FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    src, tgt, directed := false
) WHERE edge > 0;

-- 2. Pour chaque arête du chemin, recalculer SANS cette arête
-- (boucle Python nécessaire — SQL seul ne permet pas d'itérer)
```

**Limitation** : SQL nécessite un script Python qui boucle sur chaque arête,
exécute N requêtes pgr_dijkstra, et compare les résultats.
Le calcul de **betweenness centrality** (importance d'un nœud dans tous les chemins)
n'existe pas nativement en SQL.

#### Approche Graphe (Neo4j + APOC)

```cypher
// Betweenness centrality : quels POIs sont les plus "entre" les autres ?
CALL apoc.algo.betweenness('POI', 'DISTANCE', 'meters') YIELD nodeId, score
MATCH (p:POI) WHERE id(p) = nodeId
RETURN p.nom, p.role, score AS centralite
ORDER BY centralite DESC LIMIT 10;
```

**Une seule requête** pour calculer la centralité de tous les nœuds.
Pas de boucle, pas de script externe. C'est l'algorithme lui-même qui est intégré au moteur.

**Exécutez les deux approches** et comparez :
- Temps de développement (combien de lignes de code ?)
- Temps d'exécution
- Richesse du résultat (betweenness vs simple allongement)

### T2 — Requêtes croisées : là où Cypher brille

Essayez ces requêtes dans Neo4j Browser et réfléchissez à l'équivalent SQL.

#### 2a — Trouver les chemins entre deux rôles

```cypher
// Tous les chemins entre une cible d'attaque et un hôpital (défense)
MATCH path = (a:POI {role: 'attaque'})-[:DISTANCE*]-(d:POI {role: 'defense', nature: 'Hôpital'})
RETURN
    [n IN nodes(path) | n.nom] AS etapes,
    length(path) AS sauts,
    reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance_m
ORDER BY distance_m
LIMIT 5;
```

**Équivalent SQL** : il faudrait une CTE récursive qui part d'un POI,
joint sur la table de distances, vérifie qu'on n'est pas déjà passé par ce nœud,
et s'arrête quand on atteint un POI défense. ~30 lignes, difficile à maintenir.

#### 2b — Plus court chemin avec contrainte sur les nœuds intermédiaires

```cypher
// Chemin le plus court entre attaque et énergie EN PASSANT par au moins un POI ravitaillement
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

**Équivalent SQL** : deux appels pgr_dijkstra avec un nœud intermédiaire obligatoire.
Faisable mais moins lisible — et si on veut "au moins un" et pas "exactement un" ?
En Cypher, c'est un changement de pattern. En SQL, c'est une réécriture complète.

#### 2c — Sous-graphe accessible depuis un POI

```cypher
// Tous les POIs accessibles en <= 2 sauts depuis un aérodrome
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

**Équivalent SQL** : jointure récursive sur la table de distances avec `depth <= 2`.
Possible mais l'expansion se fait sur toutes les directions à la fois — Cypher
permet de filtrer par type de relation et de label dès la traversée.

### T3 — Benchmark structuré

Reproduisez ce tableau avec vos propres mesures (`EXPLAIN ANALYZE` pour SQL, `PROFILE` pour Cypher) :

| # | Requête | SQL (ms) | Cypher (ms) | Lignes de code | Lisibilité |
|---|---------|----------|-------------|----------------|------------|
| 1 | Sous-types de "Tronçon de route" | | | | |
| 2 | Tous les chemins attaque → défense | | | | |
| 3 | Betweenness centrality (choke points) | | | | |
| 4 | POIs à < 500m d'une route (`ST_DWithin`) | | | | |
| 5 | Plus court chemin avec nœud intermédiaire | | | | |

Pour chaque requête :
- Mesurez le temps avec `EXPLAIN ANALYZE` (SQL) et `PROFILE` (Cypher)
- Comptez les lignes de code nécessaires
- Notez si la requête est **impossible** ou **très complexe** dans l'autre langage

#### Détail des requêtes à exécuter :

**Requête 1 — Traversée ontologique**
```sql
-- SQL
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
```cypher
// Cypher
PROFILE MATCH path = (d:Detail)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN count(path);
```

**Requête 4 — Spatial (c'est ici que SQL gagne)**
```sql
-- SQL
EXPLAIN (ANALYZE)
SELECT count(*) FROM mission_pois p
WHERE EXISTS (
    SELECT 1 FROM troncon_de_route r
    WHERE ST_DWithin(p.geom, r.geometrie, 500)
);
```
```cypher
// Cypher — pas d'équivalent natif (pas d'index spatial)
// Il faudrait pré-calculer les distances et les stocker en relation
MATCH (p:POI) WHERE EXISTS { (p)-[:DISTANCE*]-() }
RETURN count(p);
// ↑ Cette requête ne filtre pas sur 500m — elle regarde seulement la connectivité
```

### T4 — Simulation de destruction (les deux approches)

```sql
-- SQL : bloquer une arête dans le graphe pgRouting
UPDATE ways SET cost = -1, reverse_cost = -1 WHERE id = <edge_id>;

-- Mesurer l'impact
SELECT count(*) FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    src, tgt, directed := false
) WHERE agg_cost IS NOT NULL;
```

```cypher
// Cypher : supprimer une relation dans le graphe Neo4j
MATCH (a:POI)-[r:DISTANCE]->(b:POI) WHERE r.meters > 10000 DELETE r;

// Vérifier la connectivité résiduelle
MATCH (a:POI {role: 'attaque'}), (e:POI {role: 'energie'})
RETURN EXISTS {
    (a)-[:DISTANCE*]-(e)
} AS encore_connectes;
```

**Observez** : en SQL, la destruction est un `UPDATE` sur une colonne (`cost = -1`).
En Cypher, c'est un `DELETE` sur une relation — plus naturel, plus proche du modèle mental.
La vérification de connectivité (`EXISTS { path }`) n'a pas d'équivalent SQL simple.

### T5 — Synthèse : quand utiliser quoi

Complétez ce tableau dans votre rapport :

| Situation | Outil | Pourquoi |
|-----------|-------|----------|
| Filtrer des POIs par attributs (nature, catégorie) | | |
| Calculer un buffer spatial (ST_Buffer) | | |
| Trouver le plus court chemin routier | | |
| Parcourir une hiérarchie de types | | |
| Centralité / betweenness d'un nœud | | |
| Joindre des données géographiques | | |
| Requête pattern matching (chemin multi-étapes) | | |
| Agrégation statistique (COUNT, AVG, GROUP BY) | | |

### T6 — Générer la carte de situation

```bash
python scripts/04_benchmark_comparison.py --role <votre_role> --map data/carte_situation.png
```

---

## Indices Codestral

```
"Montre un exemple concret où Cypher (Neo4j) est nettement supérieur à SQL :
trouver tous les chemins entre un aérodrome et un hôpital en passant par
au moins un réservoir, avec la distance totale. Écris le SQL équivalent
pour comparer la complexité."
```

```
"Écris une requête Cypher avec APOC pour calculer la betweenness centrality
des POIs dans un graphe de distances. Explique pourquoi cet algorithme
n'a pas d'équivalent natif en SQL pur."
```

---

## Critères de validation

- [ ] Betweenness centrality exécutée sur Neo4j (top 5 POIs identifiés)
- [ ] Requêtes 2a-2c fonctionnelles dans Neo4j Browser
- [ ] Tableau benchmark complété (5 requêtes, temps mesurés, LOC comptées)
- [ ] Requête 4 montre que SQL gagne sur le spatial (pas d'équivalent Cypher natif)
- [ ] Tableau synthèse "quand utiliser quoi" complété
- [ ] Choke points identifiés (SQL + Neo4j)
- [ ] Carte PNG générée
