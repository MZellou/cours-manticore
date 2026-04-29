---
layout: default
title: APOC — algorithmes de graphe
parent: Avancé
grand_parent: Théorie
nav_order: 1
---

# APOC — algorithmes de graphe

> **À lire avant la Phase 3.** APOC ajoute à Cypher des algorithmes absents du SQL pur (Dijkstra pondéré, subgraphes, centralité). Note : le cours utilise **Neo4j 5.x / APOC 5.x** — certaines API 4.x sont dépréciées.

---

## Qu'est-ce qu'APOC ?

**APOC** = *Awesome Procedures On Cypher*. C'est une **bibliothèque officielle** de procédures Cypher, livrée comme un plugin Neo4j.

Dans le `docker-compose.yml` du cours, APOC est déjà chargé :

```yaml
NEO4J_PLUGINS: '["apoc"]'
NEO4J_dbms_security_procedures_unrestricted: 'apoc.*'
```

Vérifier qu'il est dispo dans Neo4j Browser :

```cypher
CALL apoc.help('apoc') YIELD name RETURN count(*);
```

---

## `apoc.algo.dijkstra` — plus court chemin pondéré

> APOC 5.x : signature inchangée. Contrairement à `shortestPath()` natif (non pondéré), APOC permet de spécifier une propriété de poids sur les arêtes.

```cypher
// Trouver le chemin le plus court entre deux POIs
MATCH (start:POI {nom: 'Centrale_Flamanville'}),
      (end:POI   {nom: 'Aeroport_Brest'})
CALL apoc.algo.dijkstra(start, end, 'DISTANCE', 'meters')
YIELD path, weight
RETURN [n IN nodes(path) | n.nom] AS etapes, weight AS distance_m;
```

| Argument | Sens |
|----------|------|
| `start`, `end` | Nœuds de départ et d'arrivée |
| `'DISTANCE'` | type de relation à traverser |
| `'meters'` | propriété de poids sur la relation |

---

## `gds.betweenness.stream()` — centralité (APOC 5.x)

> **API critique** : `apoc.algo.betweenness` (4.x) est dépréciée. En APOC 5.x, la betweenness centrality passe par le catalogue GDS (*Graph Data Science*).

**Betweenness centrality** d'un nœud = nombre de plus courts chemins entre toutes les paires qui **passent par ce nœud**. Plus le score est haut, plus le nœud est un **choke point** potentiel.

```cypher
// 1. Projetter le graphe dans le catalogue GDS
CALL gds.graph.project('myGraph', 'POI', 'DISTANCE');

// 2. Calculer la betweenness sur ce graphe projeté
CALL gds.betweenness.stream('myGraph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS poi, score
RETURN poi.nom, poi.nature, poi.role, score
ORDER BY score DESC LIMIT 10;
```

> **Pourquoi c'est dur en SQL** : il faudrait N² appels Dijkstra, puis compter les passages par chaque nœud. GDS le fait en une requête sur le graphe projeté.

### Lecture du résultat

- `score` élevé = nœud **critique** (le couper isole de larges pans du réseau)
- `score = 0` = nœud "feuille" (en bout de chaîne, jamais sur un chemin)

→ Phase 3 T1 : c'est le candidat #1 pour la **stratégie offensive**.

---

## `apoc.path.subgraphAll` — sous-graphe accessible

Retourne tous les nœuds **et toutes les arêtes** atteignables depuis un point, dans une limite de profondeur.

```cypher
MATCH (centre:POI {nature: 'Aérodrome'}) LIMIT 1
CALL apoc.path.subgraphAll(centre, {
  maxLevel: 3,
  relationshipFilter: 'DISTANCE'
})
YIELD nodes, relationships
RETURN size(nodes) AS nb_pois, size(relationships) AS nb_liens;
```

| Option | Sens |
|--------|------|
| `maxLevel` | profondeur maximale (sauts) |
| `relationshipFilter` | restreindre aux relations de ce type |
| `labelFilter` | restreindre aux labels (`'+POI'` = inclure, `'-Base'` = exclure) |

→ Phase 3 T2c : sous-graphe "à 3 sauts d'un aérodrome".

---

## `allShortestPaths()` — Cypher natif

> **`allShortestPaths()` n'est pas APOC** — c'est une fonction native Cypher (== Cypher 5.x). Elle trouve tous les plus courts chemins entre deux nœuds (pas juste un).

```cypher
// Tous les chemins minimaux entre un POI attaque et un POI défense
MATCH (a:POI {role: 'attaque'}), (d:POI {role: 'défense'}),
      path = allShortestPaths((a)-[:DISTANCE*]-(d))
RETURN [n IN nodes(path) | n.nom] AS chemin,
       reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance
ORDER BY distance ASC LIMIT 5;
```

> En SQL pur, énumérer "tous les plus courts chemins" est **impossible** sans un script Python qui boucle sur Dijkstra. Cypher le fait en une ligne.

---

## `apoc.path.expandConfig` — chemin avec contraintes

Variante riche : accepte des filtres de chemin complexes (interdire un type de nœud, obliger à passer par un autre…).

```cypher
// Chemin attaque → défense en évitant les POIs énergie
MATCH (a:POI {role: 'attaque', nom: 'Centrale_Flamanville'})
CALL apoc.path.expandConfig(a, {
  relationshipFilter: 'DISTANCE',
  labelFilter: '/POI',
  blacklistedNodes: [(p:POI {role: 'énergie'}) | p],
  terminatorNodes: [(p:POI {role: 'défense'}) | p],
  maxLevel: 5
})
YIELD path
RETURN path LIMIT 3;
```

> Note APOC 5.x : `blacklistNodes` → `blacklistedNodes`.

---

## `PROFILE` — comment corriger une requête lente

Comme `EXPLAIN ANALYZE` en SQL :

```cypher
PROFILE
MATCH (p:POI)-[:DISTANCE*1..3]-(q:POI)
WHERE p.role = 'attaque' AND q.role = 'défense'
RETURN p, q LIMIT 10;
```

### Signaux d'alerte

| Métrique | Interprétation |
|----------|---------------|
| **AllNodesScan** ⚠️ | scan complet de tous les nœuds — *catastrophique* |
| **NodeIndexSeek** ✅ | utilisation d'un index — optimal |
| **Expand(All)** | traversée d'une relation |
| **db hits** élevé | beaucoup d'accès au store — risque de lenteur |

### Comment corriger

```cypher
// Si AllNodesScan sur :POI → créer un index sur le rôle
CREATE INDEX poi_role IF NOT EXISTS FOR (p:POI) ON (p.role);

// Si NodeByLabelScan sur :POI avec filtre sur nature → index composite
CREATE INDEX poi_role_nature IF NOT EXISTS FOR (p:POI) ON (p.role, p.nature);

// Si RelationshipByTypeScan (beaucoup de DbHits sur une relation) → index de relation (Neo4j 4.4+)
CREATE INDEX ON ()-[:DISTANCE]-();
```

> Après `CREATE INDEX`, relancez `PROFILE` pour vérifier que `AllNodesScan` disparaît au profit de `NodeIndexSeek` ou `NodeIndexRangeScan`.

---

## Pièges fréquents

| Symptôme | Cause probable |
|----------|---------------|
| `Procedure not found` | APOC pas chargé — vérifier `docker compose ps neo4j` |
| `gds.betweenness.stream()` échoue | Graphe pas projeté dans GDS → faire `gds.graph.project()` d'abord |
| Requête lente (beaucoup de db hits) | Manque d'index — utilisez `PROFILE` |
| `apoc.algo.dijkstra` ignore le poids | Vérifier que la propriété est **numérique**, pas string |
| `allShortestPaths` timeout | Graphe trop grand → limiter avec `maxLevel` |

---

## Pour aller plus loin

- [GraphDB 101]({% link _docs/theorie/outils/graphdb_101.md %}) — le modèle LPG et traversée de graphe
- [Cypher en 5 minutes]({% link _docs/theorie/outils/cypher_5min.md %}) — les bases
- [pgRouting et r2gg]({% link _docs/theorie/outils/pgrouting_r2gg.md %}) — routage côté PostGIS
- [Phase 3]({% link _docs/missions/phase_3_simulation.md %}) — la pratique
- [Documentation APOC 5.x](https://neo4j.com/docs/apoc/current/) (externe)
