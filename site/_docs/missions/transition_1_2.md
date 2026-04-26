---
title: Transition 1 → 2
parent: Missions
nav_order: 4
layout: default
---

# Transition Phase 1 → Phase 2

> Pause synthèse avant la cartographie. **5 minutes de lecture.**

---

## Ce que vous avez appris en Phase 1

| Compétence | Outil | Usage en Phase 2/3 |
|-----------|-------|--------------------|
| Filtrer des POIs par attributs | SQL `WHERE`, `JOIN` | Toujours utile (filtrage en amont des traitements graphe) |
| Jointures spatiales | `ST_Intersects`, `ST_DWithin` | Snap des POIs au graphe (T2) |
| Hiérarchies via récursion | `WITH RECURSIVE` | Vous allez voir l'**équivalent Cypher** en 2 lignes |
| Clustering spatial | `ST_ClusterDBSCAN` | Pas réutilisé directement, mais le réflexe "regrouper avant d'agir" reste |
| Index GIST | `CREATE INDEX … USING GIST` | Indispensable pour la Phase 2 (snap) |

> 💡 **Ce qui reste constant** : PostGIS et le SRID 2154. Tout ce qui est *spatial pur* reste en SQL.

---

## Ce qui change en Phase 2

### Du **point** au **graphe**

Phase 1 : vos POIs sont des **points isolés**. On les filtre, on les compte, on les regroupe.
Phase 2 : on ajoute la **topologie** — *qui est connecté à qui, par quel chemin, à quel coût*.

### Du **modèle linéaire** au **modèle pivot nœuds+arêtes**

Vous avez ignoré la table `troncon_de_route` jusqu'ici (trop volumineuse, peu utile pour des POIs ponctuels). En Phase 2, **r2gg** la transforme en un **graphe** (`ways` + `ways_vertices_pgr`) — c'est ce graphe que vous interrogez.

→ Lecture : [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) (5 min)

### Du **mono-paradigme SQL** au **bi-paradigme SQL + Cypher**

Vous avez écrit du SQL toute la Phase 1. Phase 2 ajoute Cypher pour :
- L'ontologie (au lieu de `WITH RECURSIVE`)
- Le réseau de POIs (relations `[:DISTANCE]`)
- Les patterns multi-étapes

→ Lecture : [Cypher en 5 minutes]({% link _docs/theorie/cypher_5min.md %}) (5 min)

---

## La grande question de Phase 2

> **À quel moment SQL est-il insuffisant ?**

Vous allez le **mesurer** :

| Tâche | Tentative SQL | Résolution Cypher / pgRouting |
|------|---------------|-------------------------------|
| Plus court chemin A → B | Impossible nativement | `pgr_dijkstra` ou `shortestPath` Cypher |
| Tous les sous-types d'une classe | `WITH RECURSIVE` (verbeux) | `(d)-[:EST_SOUS_TYPE_DE*]->(o)` |
| Tous les chemins entre A et B | Impossible | `MATCH path = (a)-[*]-(b)` |
| Graphe routier avec cost dynamique | OK avec pgRouting | Pas naturel en Cypher (quand 20M arêtes) |

→ **Conclusion anticipée** : on combine. PostGIS + pgRouting + Neo4j. Aucun outil ne suffit.

---

## Avant de cliquer "Phase 2"

- [ ] [Checkpoint Phase 1]({% link _docs/missions/checkpoint_phase_1.md %}) passé
- [ ] [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) lu
- [ ] [Cypher en 5 minutes]({% link _docs/theorie/cypher_5min.md %}) lu
- [ ] Neo4j Browser ouvert dans un onglet (`http://localhost:7474`)

---

{% include nav_phase.html prev_url="/missions/checkpoint_phase_1/" prev_label="Checkpoint Phase 1" next_url="/missions/phase_2_cartographie/" next_label="Phase 2 — Cartographie" %}
