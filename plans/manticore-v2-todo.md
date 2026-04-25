# Opération Manticore V2 — Plan de bataille (EPCI Edition)

## 1. Objectifs
- Refondre le cours BDD NoSQL (2.5J) pour ingénieurs IGN.
- Focus sur PostGIS (Spatial), pgRouting (Graphe routier) et Neo4j (Ontologie).
- Utilisation de l'IA (Mistral Vibe) pour la génération de requêtes.
- Échelle : EPCI (15 zones cibles).

## 2. Structure des FRAGOs
- **FRAGO 0 : Setup** (`00_setup.py`) — Chargement EPCI depuis Parquet (Local + CIFS).
- **FRAGO 1 : SITREP** (`01_explore_postgis.py`) — SQL récursif vs Spatial.
- **FRAGO 2 : Migration** (`02_migrate_to_neo4j.py`) — Ontologie dans Neo4j.
- **FRAGO 3 : Routage** (`03_routing_pgrouting.py`) — Itinéraires et Choke Points.
- **FRAGO 4 : Frappe** (`04_benchmark_comparison.py`) — Benchmark final et Carte.

## 3. État d'avancement

### P0 — Infrastructure & Data ✅
- [x] Fix `pyproject.toml` (hatchling build).
- [x] Dockerfile PostGIS + pgRouting.
- [x] `epci.parquet` et `commune.parquet` dans `data/`.
- [x] Chargement de l'ontologie dans PostGIS.

### P1 — Scripts TD ✅
- [x] `00_setup.py` : Filtrage EPCI + Ontologie.
- [x] `01_explore_postgis.py` : Vibe Prompts + EPCI logic.
- [x] `02_migrate_to_neo4j.py` : Migration complète.
- [x] `03_routing_pgrouting.py` : Squelette pgRouting.
- [x] `04_benchmark_comparison.py` : Script final + GeoPandas.

### P2 — Documentation ✅
- [x] `README.md` mis à jour (Liste EPCI).
- [x] `plans/theory-outline.md` (Plan 0.5J).
- [x] `docs/instructor_guide.md` (Guide Gold Dumps).

## 4. Prochaines étapes
- [ ] Tester le chargement complet sur un EPCI (ex: Brest).
- [ ] Préparer les Gold Dumps (Instructeur).
