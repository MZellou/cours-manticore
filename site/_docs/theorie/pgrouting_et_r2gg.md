---
layout: default
title: pgRouting et r2gg
parent: Théorie
nav_order: 10
---

# pgRouting et r2gg : du tronçon au plus court chemin

> **À lire avant la Phase 2.** Cette page explique *pourquoi* on a besoin d'un graphe et *comment* r2gg le construit.

---

## Le problème : un tronçon BDTOPO n'est pas un graphe

La BDTOPO stocke chaque route comme une **`LINESTRING`** avec des attributs (nature, vitesse, largeur…). Mais **rien n'y ressemble à un graphe** :

- Pas de nœuds explicites (intersections)
- Pas d'arêtes orientées avec un coût
- Pas de notion de "voisin"

Avec ce modèle, "trouver le plus court chemin entre A et B" devient :

```sql
WITH RECURSIVE chemin AS (
  -- cas de base : tronçons partant de A
  SELECT … FROM troncon_de_route WHERE …
  UNION ALL
  -- cas récursif : tronçons connectés au précédent
  SELECT … FROM chemin c JOIN troncon_de_route t ON ST_Touches(c.geom, t.geom)
  -- profondeur 5+ → plan d'exécution explose, pas d'élagage Dijkstra
)
SELECT * FROM chemin;
```

**Verdict** : possible en théorie, **impraticable** en pratique — pas de pondération, pas d'élagage, pas de Dijkstra.

---

## La solution : pivoter en graphe (r2gg)

**r2gg** (route-graph-generator) transforme la table linéaire en un schéma **nœuds + arêtes** :

```
BDTOPO (PostGIS)                      Pivot (graphe)
┌──────────────────────┐              ┌──────────────────────────┐
│ troncon_de_route     │              │ ways_vertices_pgr        │
│ ├─ geometrie (line)  │  ──r2gg──>   │ ├─ id, the_geom (point)  │
│ ├─ nature            │              │                          │
│ ├─ vitesse_moyenne   │              │ ways                     │
│ ├─ largeur_de_chaussee│             │ ├─ source, target → vertex│
│ └─ restriction_*     │              │ ├─ cost, reverse_cost     │
└──────────────────────┘              │ └─ length_m, attributs    │
                                      └──────────────────────────┘
```

Deux étapes invisibles mais cruciales :

1. **Découpage aux intersections** : un tronçon BDTOPO qui en croise un autre est *coupé* en plusieurs arêtes au point d'intersection. C'est pour ça que `count(*) FROM ways` est très différent de `count(*) FROM troncon_de_route`.
2. **Création des nœuds** (`ways_vertices_pgr`) à chaque extrémité d'arête.

> 🧠 **Le déclic** : sans découpage aux intersections, un véhicule "passerait à travers" un croisement sans pouvoir tourner. Le graphe a besoin de **nœuds aux intersections** pour modéliser les choix de l'algorithme.

---

## `cost` et `reverse_cost` — pourquoi deux colonnes ?

Une arête routière peut avoir des coûts **asymétriques** :

| `cost` (source → target) | `reverse_cost` (target → source) | Sens |
|--------------------------|----------------------------------|------|
| 100 | 100 | route à double sens |
| 100 | -1 | sens unique (interdit dans l'autre sens) |
| -1 | -1 | arête bloquée (destruction simulée Phase 3) |

> ⚠️ Convention pgRouting : **`-1` = interdit** (pas zéro, pas `NULL`).

Le coût peut être :
- la **longueur** (plus court chemin géométrique)
- le **temps** (longueur / vitesse)
- une **fonction métier** (poids véhicule, restrictions, discrétion…) — c'est le **routage contraint** vu en Phase 2 T4.

---

## Dijkstra sous pgRouting

```sql
SELECT seq, node, edge, cost, agg_cost
FROM pgr_dijkstra(
  'SELECT id, source, target, cost, reverse_cost FROM ways',
  source_vertex,    -- id du nœud départ
  target_vertex,    -- id du nœud arrivée
  directed := false
);
```

Trois éléments :

1. **La requête sur `ways`** est passée en **string** — pgRouting la lit pour construire le graphe en mémoire.
2. **`directed`** : si `true`, `cost` et `reverse_cost` sont distincts ; si `false`, on prend le plus petit des deux.
3. Le résultat est une suite ordonnée d'arêtes (pas la géométrie). Pour la carte, il faut joindre avec `ways` sur `edge = ways.id`.

---

## Comment "snapper" un POI au graphe

Un POI est un point quelconque, pas un nœud du graphe. On lui associe le **sommet le plus proche** :

```sql
SELECT
  p.cleabs,
  (SELECT id FROM ways_vertices_pgr v
   ORDER BY v.the_geom <-> p.geom
   LIMIT 1) AS vertex_id,
  ST_Distance(p.geom, v.the_geom) AS dist_snap
FROM mission_pois p;
```

> Le `<->` (KNN) utilise l'index GIST → rapide. `LIMIT 1` est essentiel.

**Si un POI a une `dist_snap` très grande**, c'est qu'il est **loin de toute route** (par exemple, en pleine forêt). Vérifier que le routage depuis ce POI a un sens.

---

## Algorithmes pgRouting utiles

| Fonction | Cas d'usage Phase 2/3 |
|----------|----------------------|
| `pgr_dijkstra` | Plus court chemin point-à-point |
| `pgr_dijkstraCostMatrix` | **Matrice** de distances entre N sources et M cibles (Phase 2 T10) |
| `pgr_drivingDistance` | **Isochrone** : tous les nœuds atteignables sous un coût max (Phase 2 T11) |
| `pgr_connectedComponents` | Composantes connexes du graphe (Phase 3 T9) |
| `pgr_aStar` | Variante avec heuristique géographique (plus rapide pour les longues distances) |

---

## Pourquoi pas Cypher pour le routage routier ?

On *pourrait* migrer le graphe routier dans Neo4j, mais :

| Critère | pgRouting | Neo4j |
|---------|-----------|-------|
| Construction du graphe | Auto via r2gg + PostGIS | À faire à la main (gros pipeline) |
| Spatial joint au routage | Natif (`ST_DWithin`) | Pas natif |
| Algorithmes Dijkstra/A* | Optimisés sur 20M arêtes | OK mais moins matures à cette taille |
| Routage **contraint** dynamique | `cost` calculé en SQL | Plus délicat |

→ **Conclusion** : pour le routage routier, on reste en pgRouting. Neo4j entre en jeu pour l'**ontologie** et le **réseau de POIs** (où Cypher excelle).

---

## Pour aller plus loin

- [PostGIS — essentiels]({% link _docs/theorie/postgis_essentiels.md %}) — pré-requis spatial
- [APOC]({% link _docs/theorie/apoc.md %}) — algorithmes côté Neo4j (betweenness, sub-graphes)
- [Phase 2]({% link _docs/missions/phase_2_cartographie.md %}) — la pratique
