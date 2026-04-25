---
title: Debriefing
parent: Missions
nav_order: 5
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

## Grille d'évaluation

| Critère | Points | Détail |
|---------|--------|--------|
| Requêtes SQL | 25% | Complexité, correction, utilisation de ST_*, WITH RECURSIVE |
| Requêtes Cypher | 20% | APOC, path patterns, comparaison SQL |
| Routage pgRouting | 20% | Dijkstra, routage contraint, choke points |
| Benchmark | 15% | Mesures chiffrées, analyse des plans de requête |
| Carte + rapport | 15% | Lisibilité, exhaustivité, conclusions |
| Présentation | 5% | Clarté, timing, participation |

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
