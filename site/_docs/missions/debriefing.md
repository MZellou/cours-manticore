---
title: Debriefing
parent: Missions
nav_order: 9
layout: default
---

# Debriefing — Livrable final

> *"Rendez votre rapport tactique et présentez vos conclusions."*

## Livrables par groupe

### 1. Carte PNG (`data/carte_situation.png`)
- POIs des 4 rôles superposés (couleurs : rouge=attaque, bleu=défense, vert=ravitaillement, orange=énergie)
- Choke points identifiés
- Routes calculées (normal + contraint)
- Impact de la destruction simulée

### 2. Rapport markdown (`rapport.md`)
Structure suggérée (2-3 pages) :
1. **SITREP** : EPCI assigné, contexte géographique
2. **Reconnaissance** : POIs par rôle (tableau + clustering)
3. **Cartographie** : itinéraires, routage contraint, matrice de distances
4. **Simulation** : choke points, impact destruction, POIs inatteignables
5. **Benchmark** : SQL vs Cypher (tableau comparatif)
6. **Conclusions** : résilience du réseau, recommandations

### 3. Présentation orale (10 min)
- 1 diapositive par phase (recon, carto, simulation)
- Focus sur les résultats concrets (pas de démo live)
- Chaque agent présente sa partie

---

## Grille de relecture des concepts

> Avant la présentation, vérifiez en équipe que **chacun** peut expliquer ces points sans relire le corrigé. C'est ce que le jury cherchera à creuser.

### Phase 1 — Spatial pur

- [ ] Pourquoi BDTOPO est en SRID 2154 (et l'effet d'un mélange 2154/4326)
- [ ] Différence `ST_Intersects` / `ST_DWithin` / `ST_Distance < N`
- [ ] Rôle de l'index GIST
- [ ] Effet de `eps` et `minpoints` sur DBSCAN
- [ ] Pourquoi `WITH RECURSIVE` est verbeux et lent en profondeur

### Phase 2 — Graphe et bi-paradigme

- [ ] Pourquoi r2gg découpe les tronçons aux intersections
- [ ] Sémantique de `cost` / `reverse_cost` et de la convention `-1`
- [ ] Comment snapper un point quelconque au sommet le plus proche (`<->`)
- [ ] Différence `MERGE` vs `CREATE` en Cypher
- [ ] Pourquoi un index Neo4j accélère drastiquement un `MERGE`
- [ ] Index-free adjacency (et pourquoi la traversée graphe est en `O(1)` par saut)

### Phase 3 — Analyse et benchmark

- [ ] Sens de la betweenness centrality (≠ degré, ≠ closeness)
- [ ] Lecture d'un plan `EXPLAIN ANALYZE` (Seq Scan vs Index Scan)
- [ ] Lecture d'un plan Cypher `PROFILE` (AllNodesScan vs NodeIndexSeek)
- [ ] Pourquoi `ST_DWithin` bat Cypher sur le spatial pur
- [ ] Pourquoi Cypher bat SQL sur les hiérarchies / réseaux
- [ ] Comment simuler proprement une coupe (backup, restore)

---

## Tableau de synthèse final (à compléter en groupe)

| Question | Outil choisi | Justification (1 phrase) | Mesure (ms / LOC) |
|----------|-------------|--------------------------|-------------------|
| Filtrer des POIs par attribut | | | |
| Calculer un buffer spatial | | | |
| Plus court chemin routier | | | |
| Tous les sous-types d'une classe | | | |
| Tous les chemins entre A et B | | | |
| Centralité d'un nœud | | | |
| Composantes connexes du réseau | | | |
| Carte tactique consolidée | | | |

> Si une case "Outil choisi" est *toujours* le même, vous avez raté le point pédagogique du cours.

---

## Pour aller plus loin

### Livres / ressources

- **PostGIS in Action** (Regina Obe & Leo Hsu) — la référence sur PostgreSQL spatial
- **Graph Databases** (Robinson, Webber, Eifrem, O'Reilly, gratuit chez Neo4j) — modèle LPG, patterns
- **Neo4j Cypher Manual** — référence officielle, très bien fait
- **pgRouting Manual** — algorithmes et exemples concrets

### Sujets non couverts mais utiles

- **GraphX / Spark GraphFrames** — graphe distribué pour très gros volumes
- **Memgraph** — alternative à Neo4j, plus rapide sur certains cas
- **PostgreSQL Custom Functions** pour combiner Cypher-like et SQL (`pg_graphql`, `Apache AGE`)
- **Routing OSM** (OSRM, Valhalla) — alternatives à pgRouting, alimentées par OpenStreetMap

### Approfondir le **routage**

- Algorithmes A*, bidirectional Dijkstra, contraction hierarchies
- Routing temps-réel avec données traffic
- Multi-modal (voiture + pied + métro)

### Approfondir le **graphe**

- Algorithmes : PageRank, Louvain (communautés), Strongly Connected Components
- Graph embeddings (node2vec, GraphSAGE) pour ML sur graphes
- Réseaux dynamiques (graphe qui change dans le temps)

---

## Commandes utiles

```bash
# Setup
python scripts/00_setup.py --epci "<EPCI>"

# Phase 1 — Reconnaissance (4h)
python scripts/01_explore_postgis.py --role <role>

# Phase 2 — Cartographie (5h)
python scripts/02_migrate_to_neo4j.py
python scripts/03_routing_pgrouting.py --role <role>

# Phase 3 — Simulation (5h)
python scripts/04_benchmark_comparison.py --role <role> --map data/carte_situation.png
```

---

{% include nav_phase.html prev_url="/missions/phase_3_simulation/" prev_label="Phase 3" %}
