---
layout: default
title: APOC — algorithmes de graphe
parent: Théorie
nav_order: 11
---

# APOC — algorithmes de graphe

> **À lire avant la Phase 3.** APOC ajoute à Cypher des algorithmes qui n'existent pas en SQL pur (betweenness, all shortest paths, sous-graphes).

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

Contrairement à `shortestPath()` natif (qui ne pondère pas), APOC permet de respecter une propriété de poids sur les relations.

```cypher
MATCH (start:POI {nom: 'Hôpital de Brest'}),
      (end:POI {nom: 'Aérodrome Brest-Guipavas'})
CALL apoc.algo.dijkstra(start, end, 'DISTANCE', 'meters')
YIELD path, weight
RETURN [n IN nodes(path) | n.nom] AS chemin, weight AS distance_totale;
```

| Argument | Sens |
|----------|------|
| `'DISTANCE'` | type de relation à utiliser |
| `'meters'` | propriété de poids sur la relation |

---

## `apoc.algo.betweenness` — centralité (choke points)

**Betweenness centrality** d'un nœud = nombre de plus courts chemins entre toutes les paires qui **passent par ce nœud**. Plus le score est haut, plus le nœud est un **point de passage critique** (choke point).

```cypher
CALL apoc.algo.betweenness(['POI'], ['DISTANCE'], 'BOTH')
YIELD node, score
RETURN node.nom, node.role, score
ORDER BY score DESC LIMIT 10;
```

| Argument | Sens |
|----------|------|
| `['POI']` | labels des nœuds à inclure |
| `['DISTANCE']` | types de relations à inclure |
| `'BOTH'` | direction (`'INCOMING'`, `'OUTGOING'`, `'BOTH'`) |

> 💡 **Pourquoi c'est dur en SQL** : il faut calculer **tous** les plus courts chemins entre **toutes** les paires de POIs (N² appels Dijkstra), puis compter les passages par chaque nœud. APOC fait ça en une procédure.

### Lecture du résultat

- `score` élevé = nœud **critique** (le couper isole de larges pans du réseau)
- `score = 0` = nœud "feuille" (en bout de chaîne, jamais sur un chemin)

→ Phase 3 T1 : c'est le candidat #1 pour la **stratégie offensive**.

---

## `apoc.path.subgraphAll` — sous-graphe accessible

Retourne tous les nœuds **et toutes les arêtes** atteignables depuis un point, dans une limite de profondeur.

```cypher
MATCH (start:POI {nom: 'Aérodrome Brest-Guipavas'})
CALL apoc.path.subgraphAll(start, {
  maxLevel: 2,
  relationshipFilter: 'DISTANCE'
})
YIELD nodes, relationships
RETURN size(nodes) AS nb_nodes, size(relationships) AS nb_edges;
```

| Option | Sens |
|--------|------|
| `maxLevel` | profondeur maximale (sauts) |
| `relationshipFilter` | restreindre aux relations de ce type |
| `labelFilter` | restreindre aux labels (`'+POI'` = inclure, `'-Base'` = exclure) |

→ Phase 3 T2c : sous-graphe "à 2 sauts d'un aérodrome".

---

## `allShortestPaths()` — tous les chemins minimaux

```cypher
MATCH (a:POI {role: 'attaque'}), (d:POI {role: 'défense'}),
      path = allShortestPaths((a)-[:DISTANCE*]-(d))
RETURN [n IN nodes(path) | n.nom] AS chemin,
       reduce(total = 0, r IN relationships(path) | total + r.meters) AS distance
ORDER BY distance ASC LIMIT 5;
```

> En SQL pur, énumérer "tous les plus courts chemins" est **impossible** sans un script Python qui boucle sur Dijkstra.

---

## `apoc.path.expandConfig` — chemin avec contraintes

Variante riche : accepte des filtres de chemin complexes (interdire un type de nœud, obliger à passer par un autre…).

```cypher
// Chemin attaque → défense en évitant tout POI énergie
MATCH (a:POI {role: 'attaque', nom: '...'})
CALL apoc.path.expandConfig(a, {
  relationshipFilter: 'DISTANCE',
  labelFilter: '/POI',
  blacklistNodes: [(p:POI {role: 'énergie'}) | p],
  terminatorNodes: [(p:POI {role: 'défense'}) | p],
  maxLevel: 5
})
YIELD path
RETURN path LIMIT 3;
```

---

## Lire un plan Cypher : `PROFILE`

Comme `EXPLAIN ANALYZE` en SQL :

```cypher
PROFILE
MATCH (p:POI)-[:DISTANCE*1..3]-(q:POI)
WHERE p.role = 'attaque' AND q.role = 'défense'
RETURN p, q LIMIT 10;
```

Ce qu'on regarde :

| Métrique | Interprétation |
|----------|---------------|
| **db hits** | nombre d'accès au store Neo4j (équivalent "tuples lus") |
| **rows** | lignes en sortie d'une étape |
| **AllNodesScan** ⚠️ | scan complet — *catastrophique*, ajoutez un index ou un label |
| **NodeIndexSeek** ✅ | utilisation d'un index — c'est ce qu'on veut |
| **Expand(All)** | traversée d'une relation |

> ⚠️ Si vous voyez **AllNodesScan** sur `:POI`, créez un index :
> `CREATE INDEX poi_role IF NOT EXISTS FOR (p:POI) ON (p.role);`

---

## Pièges fréquents

| Symptôme | Cause |
|----------|-------|
| `Procedure not found` | APOC pas chargé — vérifier `docker compose ps neo4j` et les logs |
| `betweenness` retourne tout à 0 | Type de relation mal orthographié (sensible à la casse) |
| Requête lente à mort | Manque d'index — utilisez `PROFILE` |
| `apoc.algo.dijkstra` ignore le poids | Vérifier que la propriété est numérique, pas string |

---

## Pour aller plus loin

- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — le modèle LPG
- [Cypher en 5 minutes]({% link _docs/theorie/cypher_5min.md %}) — les bases
- [Phase 3]({% link _docs/missions/phase_3_simulation.md %}) — la pratique
- [Documentation officielle APOC](https://neo4j.com/docs/apoc/current/) (externe)
