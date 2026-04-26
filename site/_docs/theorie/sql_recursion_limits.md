---
layout: default
title: SQL — limites & EXPLAIN
parent: Théorie
nav_order: 12
---

# SQL : limites de la récursion et lecture de plans

> Pourquoi SQL n'est pas l'outil idéal pour les hiérarchies profondes et les réseaux — et comment lire un plan d'exécution.

---

## Le mur du récursif

PostgreSQL supporte les CTE récursives (`WITH RECURSIVE`). Syntaxe générale :

```sql
WITH RECURSIVE hierarchy AS (
  -- Cas de base
  SELECT id, name, parent_id, 0 AS depth
  FROM bdtopo_ontology
  WHERE name = 'Tronçon de route'

  UNION ALL

  -- Cas récursif
  SELECT child.id, child.name, child.parent_id, h.depth + 1
  FROM bdtopo_ontology child
  JOIN hierarchy h ON child.parent_id = h.id
)
SELECT * FROM hierarchy ORDER BY depth;
```

Trois problèmes opérationnels :

1. **Verbeux** : 8+ lignes pour exprimer "tous les descendants".
2. **Difficile à débugger** : pas d'inspection intermédiaire facile.
3. **Pas de Dijkstra** : la CTE ne pondère pas, ne s'élague pas — elle énumère brutalement. Au-delà de 4–5 niveaux, le plan explose.

L'équivalent Cypher :

```cypher
MATCH (d)-[:EST_SOUS_TYPE_DE*]->(:Object {name: 'Tronçon de route'})
RETURN d.name;
```

→ même résultat, **2 lignes**, et la traversée est en `O(1)` par saut grâce à l'**index-free adjacency** (cf. [GraphDB 101]({% link _docs/theorie/graphdb_101.md %})).

---

## "10 jointures tuent votre base"

Règle empirique : **au-delà de 5 jointures**, l'optimiseur PostgreSQL commence à se tromper.

| Nb jointures | Comportement typique |
|-------------|---------------------|
| 1–2 | rapide, indexes B-tree efficaces |
| 3–4 | encore correct sous 100 ms |
| 5–7 | dégradation, l'optimiseur peut choisir un mauvais ordre |
| 8+ | timeout possible, plans imprévisibles |

**Pourquoi** : chaque jointure multiplie les combinaisons à explorer. PostgreSQL utilise un algo gourmand pour choisir l'ordre — au-delà d'un certain seuil (`geqo_threshold`, défaut 12), il bascule sur un algo génétique non-déterministe.

> 💡 **Réflexe** : si vous écrivez 6+ jointures pour une question "topologique" (réseau, hiérarchie), c'est probablement un signal pour **changer d'outil** (Cypher).

---

## Lire `EXPLAIN ANALYZE`

`EXPLAIN` montre le plan **sans exécuter**. `EXPLAIN ANALYZE` **exécute** la requête et reporte les temps réels.

```sql
EXPLAIN ANALYZE
SELECT count(*)
FROM mission_pois p
JOIN ways_vertices_pgr v
  ON ST_DWithin(p.geom, v.the_geom, 100);
```

Sortie typique (lecture **bottom-up**) :

```
Aggregate  (cost=12345.00 rows=1) (actual time=423.5..423.5 rows=1 loops=1)
  ->  Nested Loop  (cost=10.0..12000.0 rows=1234 ...)
        ->  Seq Scan on mission_pois p   ⚠️
              (cost=0.00..150.0 rows=200)
        ->  Index Scan using idx_vertices_geom on ways_vertices_pgr v
              Index Cond: (v.the_geom && st_expand(p.geom, 100))
              Filter: ST_DWithin(p.geom, v.the_geom, 100)
```

Ce qu'il faut savoir lire :

| Étape | Bon signe ✅ | Mauvais signe ⚠️ |
|-------|-------------|------------------|
| Accès table | `Index Scan`, `Bitmap Index Scan` | `Seq Scan` sur grande table |
| Jointure | `Nested Loop` (petites tables), `Hash Join` | `Nested Loop` sur 2 grandes tables sans index |
| Tri | déjà trié par index | `Sort` après lecture d'index |
| **Coût estimé vs réel** | proche | très divergent → stats périmées (`ANALYZE table`) |

### Comment savoir si une requête est lente

`actual time` est en millisecondes. Le **dernier nœud** affiche le total.

```
Planning Time: 0.5 ms
Execution Time: 423.5 ms       ← le chiffre qui compte
```

### Astuces

- `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` ajoute les stats d'I/O (cache hits / disk reads).
- Pour comparer **2 requêtes équivalentes**, on regarde `Execution Time` et la structure du plan, pas le `cost` (estimé, pas mesuré).

---

## Cypher PROFILE = équivalent

```cypher
PROFILE
MATCH (d)-[:EST_SOUS_TYPE_DE*]->(:Object {name: 'Tronçon de route'})
RETURN d.name;
```

| SQL | Cypher |
|-----|--------|
| `EXPLAIN` | `EXPLAIN` |
| `EXPLAIN ANALYZE` | `PROFILE` |
| `actual time=...` | `db hits=...` (nombre d'accès au store) |
| `Seq Scan` | `AllNodesScan` |
| `Index Scan` | `NodeIndexSeek` |

→ Détails dans [APOC]({% link _docs/theorie/apoc.md %}#lire-un-plan-cypher--profile).

---

## Phase 3 : ce qu'on benchmarke

| # | Requête | Outil naturel | Pourquoi |
|---|---------|---------------|----------|
| 1 | Sous-types ontologiques | **Cypher** | `[*]` vs `WITH RECURSIVE` |
| 2 | Tous les chemins A→B | **Cypher** | impossible nativement en SQL |
| 3 | Betweenness centrality | **Cypher + APOC** | nécessiterait N² Dijkstra en SQL |
| 4 | POIs à < 500 m d'une route | **PostGIS** | `ST_DWithin` + index GIST natif |
| 5 | Plus court chemin avec nœud intermédiaire | **Cypher** | 2 patterns, vs 2 Dijkstra + collage |

Vous mesurerez **`Execution Time`** côté SQL et **`db hits`** côté Cypher.

---

## Pour aller plus loin

- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — pourquoi la traversée graphe est en `O(1)`
- [APOC]({% link _docs/theorie/apoc.md %}) — algorithmes côté Cypher
- [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) — Dijkstra sous SQL
