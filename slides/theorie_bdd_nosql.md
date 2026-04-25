---
marp: true
theme: default
paginate: true
---

# Opération Manticore

## Bases de données NoSQL & Analyse spatiale tactique

_Cours MSST/IGN — 0.5J théorie + 2J TD_

---

# Pourquoi ce cours ?

**BDTOPO** = 20M+ routes, 600k zones d'intérêt, hiérarchie 3 niveaux

Les bases relationnelles atteignent leurs limites :
- **Récursion profonde** → `WITH RECURSIVE` devient illisible et lent
- **Réseaux** → pas de traversée de graphe native en SQL
- **Spatial** → PostGIS compense, mais le routage topologique nécessite pgRouting

---

# Objectifs du TD

Vous êtes **agents militaires** assignés à un EPCI

3 phases :
1. **Reconnaissance** → identifier les POIs critiques (PostGIS)
2. **Cartographie** → routes et combinaisons optimales (pgRouting + Neo4j)
3. **Simulation** → destruction et résilience (benchmark SQL vs Cypher)

---

# Rappels SQL & ACID

**ACID** = Atomicité, Cohérence, Isolation, Durabilité

Garanties du modèle relationnel... mais à quel coût ?

> Toute jointure supplémentaire multiplie la complexité

---

# Le mur du récursif

```sql
WITH RECURSIVE hierarchy AS (
    SELECT id, name, parent_id, 0 AS depth
    FROM ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT c.id, c.name, c.parent_id, h.depth + 1
    FROM ontology c JOIN hierarchy h ON c.parent_id = h.id
)
SELECT * FROM hierarchy;
```

**Problème** : syntaxe lourde, difficile à débugger, dégradation exponentielle

---

# 10 jointures tuent votre base

- Jointure 1-2 : rapide (index B-tree)
- Jointure 3-4 : ça ralentit
- Jointure 5+ : le plan d'exécution explose
- Jointure 10 : timeout

**Alternative** : traversée de graphe en O(1) par nœud (index-free adjacency)

---

# Le théorème CAP

```
      Consistency
         /\
        /  \
       /    \
  A  /      \  P
 Availability  Partition tolerance
```

> En réseau distribué, on ne peut garantir que 2 des 3 à la fois

---

# Panorama NoSQL

| Type | Exemple | Force | Limite |
|------|---------|-------|--------|
| Clé-Valeur | Redis | Latence ultra-faible | Pas de requêtes complexes |
| Document | MongoDB | Schéma flexible | Pas de jointures |
| Colonne | Cassandra | Scalabilité massive | Requêtes limitées |
| **Graphe** | **Neo4j** | **Traversées rapides** | **Scaling horizontal** |

---

# Modèle LPG (Labeled Property Graph)

**Nœuds** : entités avec labels et propriétés

```cypher
(:Person {name: "Agent Dupont", role: "attaque"})
(:POI {type: "aérodrome", nom: "Brest-Guipavas"})
(:ClasseOntologie {name: "Tronçon de route"})
```

**Relations** : arêtes typées avec propriétés

```cypher
(:Detail)-[:EST_SOUS_TYPE_DE]->(:Object)
(:POI)-[r:DISTANCE {meters: 5400}]->(:POI)
```

---

# Index-Free Adjacency

Dans Neo4j, chaque nœud stocke directement les pointeurs vers ses voisins.

```
BDD relationnelle : O(log n) par jointure indexée
Neo4j : O(1) par traversée → pas d'index nécessaire
```

**Conséquence** : les requêtes de graphe sont **constantes** en complexité par saut

---

# Cypher vs SQL

**SQL** : "Trouve les enfants de X où Y = Z"
```sql
SELECT c.* FROM child c JOIN parent p ON c.parent_id = p.id WHERE p.name = 'X';
```

**Cypher** : "Trouve les enfants de X"
```cypher
MATCH (c)-[:CHILD_OF]->(p {name: 'X'}) RETURN c;
```

Pattern matching déclaratif → proche de la façon dont on pense le graphe

---

# PostGIS : Intelligence spatiale

- **Géométries** : Point, LineString, Polygon (SRID 2154 = Lambert-93)
- **Index GIST** : accélération des opérations spatiales
- **Opérations** : `ST_Intersects`, `ST_DWithin`, `ST_Buffer`, `ST_ClusterDBSCAN`

```sql
SELECT * FROM pois WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(2.3,48.9),4326)::geography, 5000);
```

---

# Topologie vs Géométrie

**Géométrie** : où sont les choses ? → `ST_Intersects`, `ST_Contains`

**Topologie** : comment sont-elles connectées ? → graphe (sommets + arêtes)

> Un pont coupe une rivière = géométrie
> Supprimer le pont force un détour de 15km = topologie

**pgRouting** travaille sur la topologie, pas la géométrie

---

# pgRouting : Dijkstra

```sql
SELECT seq, node, edge, cost, agg_cost
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    source_vertex, target_vertex, directed := false
);
```

- `ways` : arêtes du graphe routier
- `cost` : temps ou distance (personnalisable)
- `directed := false` : routes à double sens

---

# Routage contraint

Le coût peut être dynamique selon le contexte :

| Contrainte | Clause SQL |
|-----------|------------|
| Poids lourds | `cost = -1 IF restriction_poids` |
| Convois larges | `cost = -1 IF largeur < 4m` |
| Discrétion | `cost * 0.7` pour chemins secondaires |
| Urgence | `cost * 0.5` pour autoroutes |

---

# SQL vs Cypher : benchmark

Même requête (sous-types ontologiques) :

| Critère | PostgreSQL (WITH RECURSIVE) | Neo4j (Cypher) |
|---------|---------------------------|----------------|
| Lisibilité | ⚠️ Verbeux | ✅ Concis |
| Performance | Se dégrade avec la profondeur | Constant par saut |
| Plan d'exécution | EXPLAIN ANALYZE | PROFILE |
| Jointure spatiale | ✅ ST_Intersects native | ❌ Pas natif |

**Conclusion** : le bon outil pour la bonne tâche

---

# IA pour la génération de requêtes

**Codestral CLI** (Mistral) → votre assistant de codage

```
> "Écris une requête Cypher pour trouver tous les POIs de type
   'aérodrome' connectés à un poste de transformation par un
   chemin de distance < 10km"
```

L'IA ne remplace pas la compréhension, mais accélère l'itération.

---

# Résumé

1. **PostGIS** → requêtes spatiales (POIs, zones)
2. **pgRouting** → routage topologique (Dijkstra, contraintes)
3. **Neo4j** → ontologie et combinaisons (Cypher, APOC)
4. **Benchmark** → SQL vs Cypher (mesurer, pas deviner)

**Prochaine étape** : briefing opérationnel → votre EPCI vous attend.
