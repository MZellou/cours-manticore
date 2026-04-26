---
layout: default
title: Cypher en 5 minutes
parent: Théorie
nav_order: 9
---

# Cypher en 5 minutes

> Lisez ceci **avant la Phase 2**. Vous saurez écrire des requêtes Cypher de base et les déboguer dans Neo4j Browser.

---

## L'idée en une phrase

> Cypher est un **langage de pattern matching** : on dessine ce qu'on cherche dans le graphe avec des parenthèses (nœuds) et des crochets (relations).

```cypher
(:POI {role: 'attaque'})-[:DISTANCE]->(:POI {role: 'défense'})
//   nœud + label + propriétés       relation typée    autre nœud
```

---

## Les 4 verbes de base

### `MATCH` — trouve un pattern

```cypher
// Tous les POI rôle attaque
MATCH (p:POI {role: 'attaque'})
RETURN p.nom, p.source LIMIT 10;
```

### `WHERE` — filtre

```cypher
MATCH (p:POI)
WHERE p.role = 'défense' AND p.nature = 'Hôpital'
RETURN p.nom;
```

### `CREATE` / `MERGE` — crée un nœud ou une relation

- `CREATE` → crée systématiquement (peut faire des doublons)
- `MERGE` → crée seulement si ça n'existe pas déjà (idempotent)

```cypher
// Créer une base avancée
CREATE (b:Base {nom: 'PC tactique', lon: -4.5, lat: 48.4});

// Idempotent : ré-exécuter la requête ne fait pas de doublon
MERGE (b:Base {nom: 'PC tactique'})
  ON CREATE SET b.lon = -4.5, b.lat = 48.4;
```

### `RETURN` — sélectionne ce qu'on veut voir

```cypher
MATCH (p:POI)
RETURN p.role AS role, count(*) AS n
ORDER BY n DESC;
```

---

## Direction des relations

Les relations sont **toujours orientées** dans Neo4j (même quand on s'en fiche).

| Pattern | Sens |
|---------|------|
| `(a)-[:R]->(b)` | de `a` vers `b` (orienté) |
| `(a)<-[:R]-(b)` | de `b` vers `a` |
| `(a)-[:R]-(b)` | sans direction (les deux sens) |

Dans ce TD, `[:DISTANCE]` est conceptuellement **non-orientée** (la distance A→B = B→A) → utilisez `-[:DISTANCE]-`.
La relation `[:EST_SOUS_TYPE_DE]` est **orientée** (un Detail est sous-type d'un Object).

---

## Pattern de chemin : la killer feature

### Chemin de longueur fixe

```cypher
// Voisins directs d'un POI
MATCH (p:POI {nom: 'Hôpital de Brest'})-[:DISTANCE]-(voisin:POI)
RETURN voisin.nom, voisin.role;
```

### Chemin de longueur variable

```cypher
// Tous les sous-types (à n'importe quelle profondeur)
MATCH (d)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN d.name;
```

`*` = profondeur quelconque. `*1..3` = de 1 à 3 sauts.

> 💡 **C'est ici que Cypher écrase SQL** : pas de `WITH RECURSIVE`, juste un `*`.

---

## `OPTIONAL MATCH` — la jointure externe

Comme `LEFT JOIN` en SQL : si le pattern n'existe pas, on retourne `NULL`.

```cypher
// Liste tous les POIs et leur nombre de voisins (0 si isolés)
MATCH (p:POI)
OPTIONAL MATCH (p)-[r:DISTANCE]-(:POI)
RETURN p.nom, count(r) AS nb_voisins
ORDER BY nb_voisins ASC;
```

→ POI avec `nb_voisins = 0` = îlot dans le graphe.

---

## `UNWIND` — aplatir une liste en lignes

```cypher
UNWIND ['attaque', 'défense', 'énergie', 'ravitaillement'] AS r
MATCH (p:POI {role: r})
RETURN r, count(p) AS nb;
```

Utile pour itérer sur un set de valeurs sans union.

---

## `WITH` — chaîner des étapes

`WITH` joue le rôle de pipeline : il passe les résultats d'une étape à la suivante.

```cypher
// Top 5 POI par nombre de voisins
MATCH (p:POI)-[:DISTANCE]-(v:POI)
WITH p, count(v) AS degree
ORDER BY degree DESC
LIMIT 5
RETURN p.nom, p.role, degree;
```

---

## Cypher vs SQL — équivalences mentales

| Cypher | SQL |
|--------|-----|
| `MATCH (p:POI)` | `SELECT * FROM POI` |
| `WHERE` | `WHERE` |
| `RETURN p.nom, count(*)` | `SELECT nom, count(*)` |
| `MATCH (a)-[:R]-(b)` | `JOIN ... ON a.id = b.a_id` |
| `MATCH (a)-[:R*]-(b)` | `WITH RECURSIVE ...` (verbeux) |
| `OPTIONAL MATCH` | `LEFT JOIN` |
| `MERGE` | `INSERT ... ON CONFLICT DO NOTHING` |
| `UNWIND` | `SELECT ... FROM unnest(...)` |
| `ORDER BY ... LIMIT` | idem |

---

## Déboguer dans Neo4j Browser

Ouvrez `http://localhost:7474`.

| Outil | À quoi ça sert |
|-------|---------------|
| `EXPLAIN <query>` | montre le plan **sans exécuter** |
| `PROFILE <query>` | exécute + montre les hits par étape (équivalent `EXPLAIN ANALYZE`) |
| `:schema` | liste labels + propriétés indexées |
| `CALL db.indexes()` | index existants |

> Toujours **lire le plan** quand une requête est lente. Le coupable est presque toujours une étape sans index.

---

## Pour aller plus loin

- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — le modèle LPG complet
- [APOC]({% link _docs/theorie/apoc.md %}) — algorithmes (betweenness, sub-graphes)
- [Phase 2]({% link _docs/missions/phase_2_cartographie.md %}) — passer à la pratique
