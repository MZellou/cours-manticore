---
layout: default
title: Pourquoi ce cours
parent: Théorie
nav_order: 1
---

# Pourquoi ce cours ?

> Cette page remplace les slides théoriques. Elle se lit en **15 minutes** et pose les fondations qui rendent les 3 phases du TD compréhensibles.

---

## Le problème : la BDTOPO atteint les limites du SQL pur

La **BDTOPO** (IGN) contient :

- **20 M+ tronçons de route**
- **600 k zones d'intérêt** (hôpitaux, gendarmeries, zones industrielles…)
- Une **ontologie hiérarchique** sur 3 niveaux (Database → Object → Detail)

Trois types de questions deviennent douloureuses en SQL pur :

| Type de question | Exemple BDTOPO | Pourquoi SQL souffre |
|------------------|---------------|----------------------|
| **Récursion profonde** | "Tous les sous-types de Tronçon de route" | `WITH RECURSIVE` → verbeux, lent quand la profondeur croît |
| **Réseaux** | "Plus court chemin de A à B" | Aucune traversée de graphe native — il faudrait écrire Dijkstra à la main |
| **Spatial pur sans topologie** | "Tronçons à moins de 500 m d'un hôpital" | OK, PostGIS le gère, mais pas le routage |

> **Le cours n'oppose pas SQL et NoSQL** : il montre **comment combiner** PostGIS (spatial) + pgRouting (graphe routier) + Neo4j (ontologie/réseau).

---

## Ce que vous allez réellement faire

Vous êtes **agents de renseignement** assignés à un EPCI :

| Phase | Outil principal | Ce que vous touchez |
|-------|----------------|---------------------|
| 🔍 [Phase 1 — Reconnaissance]({% link _docs/missions/phase_1_reconnaissance.md %}) | **PostGIS** | SQL spatial, `ST_Intersects`, `ST_ClusterDBSCAN`, ontologie via `WITH RECURSIVE` |
| 🗺️ [Phase 2 — Cartographie]({% link _docs/missions/phase_2_cartographie.md %}) | **pgRouting + Neo4j** | r2gg, Dijkstra, migration POIs en Cypher, OPTIONAL MATCH |
| 📊 [Phase 3 — Simulation]({% link _docs/missions/phase_3_simulation.md %}) | **Cypher + APOC** | Betweenness, benchmark `EXPLAIN ANALYZE` vs `PROFILE`, simulation destructive |

---

## Rappel ACID, et pourquoi BASE existe

**ACID** (SQL classique) : Atomicité, Cohérence, Isolation, Durabilité.
Le contrat dur du transactionnel — fiable, mais coûteux à passer à l'échelle horizontale.

**BASE** (typique NoSQL distribué) : Basically Available, Soft state, Eventually consistent.
On relâche la cohérence stricte pour gagner en disponibilité et passer à l'échelle.

> Dans ce TD, **PostgreSQL et Neo4j sont tous deux ACID** (mono-nœud). On n'a pas de problème de partitions.
> Ce qui justifie le changement, ce n'est **pas** CAP — c'est le **modèle de données**.

---

## Le théorème CAP (mémo)

Dans un **système distribué**, on ne peut garantir que **2 sur 3** :

```
       Consistency
          /\
         /  \
        /    \
   A  /      \  P
Availability  Partition tolerance
```

| Système | Choix typique | Pourquoi |
|---------|---------------|----------|
| PostgreSQL | CA | Mono-leader, on coupe la dispo si partition |
| Neo4j | CA | Idem (single-node par défaut, cluster en CP) |
| Cassandra | AP | Eventually consistent par design |
| MongoDB | CP | Cohérence stricte, sacrifie la dispo en cas de partition |

---

## Panorama NoSQL — 4 familles

| Famille | Modèle | Exemple | Cas d'usage |
|---------|--------|---------|-------------|
| Clé-Valeur | Dictionnaire géant | Redis, DynamoDB | Cache, sessions, compteurs |
| Document | JSON hiérarchique | MongoDB, CouchDB | Catalogues, CMS, API REST |
| Colonne | Lignes creuses massives | Cassandra, HBase | Time-series, logs, IoT |
| **Graphe** | **Nœuds + relations typées** | **Neo4j** | **Réseaux, ontologies, routage** |

→ **Pourquoi Neo4j ici** : la BDTOPO a une ontologie hiérarchique connectée + des POIs liés par des distances. Le modèle graphe capture ça nativement.

---

## Le déclic : index-free adjacency

**SQL** : pour trouver les voisins d'un nœud, on cherche dans un **index** (`O(log n)`).
**Neo4j** : chaque nœud stocke directement les **pointeurs** vers ses voisins (`O(1)` par saut).

```
SQL :   SELECT * FROM edges WHERE source_id = 42;   → index B-tree
Neo4j : MATCH (n)-[r]->(m) WHERE id(n) = 42         → pointeur direct
```

**Conséquence** : la traversée de graphe ne ralentit pas avec la taille de la base. Seul le **degré** du nœud compte.

[→ Détail dans GraphDB 101]({% link _docs/theorie/graphdb_101.md %})

---

## Le couple gagnant : SQL spatial + graphe

Aucun outil ne suffit seul. Le **bon réflexe** :

| Question | Outil approprié |
|----------|-----------------|
| Filtre attributaire (`nature`, `categorie`) | SQL |
| Spatial (`ST_Intersects`, `ST_DWithin`) | PostGIS |
| Plus court chemin routier | pgRouting (graphe en SQL) |
| Hiérarchie ontologique profonde | Cypher / Neo4j |
| Centralité, betweenness, sous-graphes | Cypher + APOC |

C'est ce que vous allez **mesurer** en Phase 3.

---

## L'IA dans ce TD

Vous avez accès à un LLM (Codestral CLI, Claude, ChatGPT…). C'est votre **co-pilote**, pas votre béquille :

- ✅ "Explique-moi pourquoi `pgr_dijkstra` utilise `cost` ET `reverse_cost`"
- ✅ "Compare la complexité d'un `WITH RECURSIVE` à 5 niveaux vs un `MATCH (a)-[*]-(b)`"
- ✅ "Pourquoi mon `ST_DWithin` retourne 0 résultats alors que les géométries semblent proches ?" *(indice probable : SRID)*
- ❌ "Donne-moi la solution copier-coller de la T3" → vous saurez l'exécuter mais pas la défendre.

Les **corrigés sont ouverts**. Le LLM est ouvert. La seule chose qui compte : **comprendre pourquoi**.

---

## Pour la suite

- [NoSQL vs SQL]({% link _docs/theorie/nosql_vs_sql.md %}) — quand changer de paradigme
- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — le modèle LPG en détail
- [Modèle BDTOPO]({% link _docs/theorie/bdtopo.md %}) — les données du TD
- [PostGIS — essentiels]({% link _docs/theorie/postgis_essentiels.md %}) — SRID, géométries, DBSCAN
- [Cypher en 5 minutes]({% link _docs/theorie/cypher_5min.md %}) — avant la Phase 2
- [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) — pourquoi un graphe ?
- [APOC : algorithmes de graphe]({% link _docs/theorie/apoc.md %}) — pour la Phase 3
- [SQL : limites de la récursion]({% link _docs/theorie/sql_recursion_limits.md %}) — `EXPLAIN ANALYZE`
