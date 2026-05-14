# Validation croisée — 4 rôles × 4 EPCIs

> 240 outputs exécutés le 2026-05-14
> Stats : **158 OK** | **50 Tiny** | **10 Empty** | **22 Error**

## Structure

```
validation/
  attaque/         — Brest Métropole (242900314)
    epci.txt
    phase1/phase2/phase3/
  defense/         — Grenoble-Alpes-Métropole (200040715)
    epci.txt
    phase1/phase2/phase3/
  ravitaillement/  — Le Havre Seine Métropole (200084952)
    epci.txt
    phase1/phase2/phase3/
  energie/         — CU de Dunkerque (245900428)
    epci.txt
    phase1/phase2/phase3/
```

## Setup par rôle

| Rôle | EPCI | SIREN | POIs | Routes | Vertices | DISTANCE rels |
|------|------|-------|------|--------|----------|---------------|
| Attaque | Brest Métropole | 242900314 | 1,119 | 69,692 | 53,990 | ~1.3M |
| Défense | Grenoble-Alpes-Métropole | 200040715 | 487 (+3 others) | 69,692 | 53,990 | ~1.3M |
| Ravitaillement | Le Havre Seine Métropole | 200084952 | 2,147 | 41,248 | 31,481 | ~2.9M |
| Énergie | CU de Dunkerque | 245900428 | 1,836 | 34,122 | 26,004 | ~3.8M |

Note : Défense a été validé sur Grenoble mais avec les POIs des 4 rôles accumulés dans mission_pois.

## Résultats par phase

### Phase 1 — Reconnaissance (PostGIS + DuckDB)

| Task | Attaque | Défense | Ravitaillement | Énergie | Notes |
|------|---------|---------|----------------|---------|-------|
| T0a | OK (59f) | OK | OK | OK | DuckDB → corrigés corrigés en Fix #6 |
| T0b | OK (31f) | OK | OK | OK | Spatial joins fonctionnels |
| T1 | OK | ERROR | ERROR | ERROR | Ontologie CTE: `hopital`/`hôpital` ne matche pas d'enfants dans certains EPCIs |
| T2 | OK | OK (487) | OK (2,147) | OK (1,836) | Quantités très variables par rôle |
| T3 | OK | OK | OK | OK | Buffer analysis OK pour tous |
| T4 | OK | OK | OK | OK | Clustering DBSCAN OK |
| T5 | OK | OK | SMALL (4) | SMALL (4) | Cross-role: attaque a +de données proches |
| T7 | OK | OK | OK | OK | Multi-role clusters |
| B1 | OK | ERROR | ERROR | ERROR | `construction_ponctuelle` filtre absent dans certains EPCIs |
| B7 | OK | TINY | TINY | TINY | Réservoirs: 0 lignes sauf Brest |

### Phase 2 — Cartographie Neo4j

| Task | Attaque | Défense | Ravitaillement | Énergie | Notes |
|------|---------|---------|----------------|---------|-------|
| T0 | OK | OK | OK | OK | Labels OK |
| T1 | OK | OK | OK | OK | Counts par label |
| T2 | OK | EMPTY | EMPTY | EMPTY | Ontologie tree: `Bâtiment` pas trouvé |
| T3 | OK | OK | OK | OK | POI details par rôle |
| T4 | OK | OK | OK | OK | DISTANCE relationships |
| T5 | OK | OK | OK | OK | Nearest neighbors |
| T6 | — | EMPTY | EMPTY | EMPTY | POI→ontologie: pas de relation EST_SOUS_TYPE_DE sur POIs |
| T7 | OK | OK | TIMEOUT | EMPTY | Cross-role: heavy avec 2.9M+ rels |
| T8 | OK | OK | TIMEOUT | OK | Shortest path: timeout sur Le Havre |
| T9 | TIMEOUT | OK | TIMEOUT | OK | Pattern matching: OOM avec graphes denses |
| T10 | OK | OK | TIMEOUT | OK | Aggregation par source |

### Phase 3 — Simulation & Benchmark

| Task | Attaque | Défense | Ravitaillement | Énergie | Notes |
|------|---------|---------|----------------|---------|-------|
| T0 | OK | OK | OK | OK | Road network stats |
| T1a | OK | OK | OK | OK | Dijkstra basique |
| T1b | OK | ERROR | ERROR | ERROR | POI→vertex snap + Dijkstra: erreurs sur certains EPCIs |
| T2a | OK | ERROR | ERROR | ERROR | K-shortest paths |
| T2b | OK | OK | OK | OK | Constrained routing |
| T3 | OK | ERROR | ERROR | ERROR | Isochrones (driving distance) |
| T4 | OK | ERROR | ERROR | ERROR | Choke points |
| T5 | OK | OK | OK | OK | Benchmark SQL vs Cypher |
| T6 | OK | ERROR | ERROR | ERROR | Situation map |

## 🔴 EMPTY outputs (0 lignes) — Investigation needed

Ces fichiers sont complètement vides. La requête a retourné 0 résultats :

| Fichier | Raison probable |
|---------|----------------|
| `{defense,ravitaillement,energie}/phase2/T2_1` | No `Bâtiment` node in ontology tree |
| `{defense,ravitaillement,energie}/phase2/T2_2` | Same — path query returns nothing |
| `{defense,ravitaillement,energie}/phase2/T6_1` | POIs don't have `EST_SOUS_TYPE_DE` links to ontology |
| `energie/phase2/T7_1` | Cross-role query empty (3.8M rels → maybe not filtered correctly) |

## 🟠 ERROR outputs — Requêtes qui plantent

### Phase 1
- **B1** (defense, ravitaillement, energie): `construction_ponctuelle` filter `nature IN ('Tour', ...)` returns nothing outside Brest
- **B7** (defense, ravitaillement, energie): Same — reservoir count returns empty
- **T1_1** (defense, ravitaillement, energie): Ontology CTE for `hopital`/`hôpital` returns 0 children (different data)

### Phase 3 (defense, ravitaillement, energie)
- **T1b_1, T2a_1, T3_1, T4_1, T6_1**: pgRouting queries failing — likely `pgr_dijkstra` returns no path (disconnected components or vertex IDs out of range)
- **T2b_2** (ravitaillement, energie): `constrained_edges_view` doesn't exist

## 🟡 TINY outputs (1 line) — Low value pour le cours

### Attaque Phase 2 (legacy validation)
Beaucoup de tâches avancées GDS/cypher sont à 1 ligne :
- `T1_betweenness`, `T1_gds_project` — GDS non installé (fixé dans docker-compose)
- `T9_avoid_energy`, `T9_via_energy` — OOM (fixé avec `*1..3`)
- `T5_*` — Tasks de manipulation de graphe (coupe/restaure d'edges)
- `T7_*`, `T8_*` — Opérations de destruction de noeuds

### Autres rôles
- **B7** (defense, ravitaillement, energie) — Réservoirs vides en dehors de Brest
- **ravitaillement Phase 2**: T7-T9 timeout sur graphes denses (2.9M rels)
- **energie/defense Phase 3 T5_1** — `\timing` output only

## Stats résumées (post-fix v2)

**0 ERROR** | 182 OK | 13 zero_rows | 5 EMPTY | 41 tiny

| Rôle | total | OK | 0 rows | EMPTY | tiny |
|------|-------|----|--------|-------|------|
| Attaque (Brest) | 93 | 58 | 3 | 0 | 32 |
| Défense (Grenoble) | 48 | 43 | 1 | 1 | 3 |
| Ravitaillement (Le Havre) | 50 | 41 | 4 | 2 | 3 |
| Énergie (Dunkerque) | 50 | 40 | 5 | 2 | 3 |

### EMPTY restants (5) — pas des bugs cours

| Fichiers | Raison |
|----------|--------|
| `{defense,ravit,energie}/P2/T2_2` (3) | Validation script: arrow direction dans Cypher. Corrigés utilisent la bonne direction. |
| `{ravit,energie}/P2/T7_1` (2) | Cross-role DISTANCE vide car POIs d'EPCIs différents (Le Havre ≠ Dunkerque ≠ Brest/Grenoble). En TD réel, même EPCI → OK. |

### Attaque tiny (32) — legacy run

L'ancien script de validation (attaque) était moins complet. Ces fichiers sont de l'ancien run et documentent des problèmes déjà fixés (GDS, `*1..3` bounding, etc.).

| # | Fichier | Fix |
|---|---------|-----|
| 1 | `docker-compose.yml` | Ajouté GDS plugin + 2G heap + 2G transaction max |
| 2 | `scripts/03_routing_pgrouting.py` | Double quotes `''Chemin''` → `'Chemin'` |
| 3 | — | Labels `:Object`/`:Detail` — faux positif confirmé |
| 4 | `scripts/02_migrate_to_neo4j.py` | MERGE `{cleabs, role}` composite key + spatial pre-filter + batching |
| 5 | `pages/corriges/phase_2.qmd` | `[:DISTANCE*]` → `[:DISTANCE*1..3]` + note |
| 6 | `pages/corriges/phase_3.qmd` | Same fix + note |
| 7 | `pages/corriges/phase_1.qmd` | DuckDB `read_parquet()` + callout colonnes manquantes |
