# Opération Manticore — Cours BDD NoSQL (Graph + Spatial)

**Format** : 0.5J théorie + 2J TD | **Stack** : PostGIS + pgRouting + Neo4j

> 🎯 Projet immersif : équipes d'agents militaires cartographiant les infrastructures critiques d'un EPCI.

📖 **Site du cours** : voir le dossier `site/` (Jekyll + just-the-docs, déployé via GitHub Pages)

---

## Quick start (étudiant)

```bash
git clone --recurse-submodules <repo-url> && cd cours-manticore
cp rclone.conf.example rclone.conf  # fill your R2 credentials
cp .env.example .env
make setup                          # pull data + docker + uv
python scripts/00_setup.py --epci "<votre EPCI>"
```

### Commandes utiles

```bash
make help          # toutes les commandes disponibles
make data-pull     # pull données depuis R2
make data-push     # push données vers R2 (prof only)
make up            # démarrer PostGIS + Neo4j
make down          # arrêter les conteneurs
make clean         # arrêter + supprimer volumes
```

---

## Structure

```
site/                     # GitHub Pages (Jekyll + just-the-docs)
  _pages/                 # Contenu du cours (missions, rôles, théorie)
scripts/                  # Scripts Python (setup + phases 1-4)
  00_setup.py             # Load EPCI + Ontology + nuclear plants
  01_explore_postgis.py   # Phase 1: POI queries + ST_ClusterDBSCAN
  02_migrate_to_neo4j.py  # Phase 2: Ontology + POIs → Neo4j
  03_routing_pgrouting.py # Phase 2+3: Dijkstra + constrained routing
  04_benchmark_comparison.py  # Phase 3: SQL vs Cypher benchmark
  admin_generate_gold_dumps.py  # Instructor: r2gg for 10 EPCIs
mission/                  # Briefings étudiant (source markdown)
  roles/{attaque,defense,ravitaillement,energie}.md
docker-compose.yml        # PostGIS + Neo4j
docker-compose.routing.yml  # OSRM + Valhalla (optional)
postgres-pgrouting.Dockerfile
pyproject.toml            # Python deps (uv)
Makefile                  # Student setup automation
rclone.conf.example       # Template R2 credentials
```

---

## Instructeur

- `make data-push` pour uploader les données sur R2
- `python scripts/admin_generate_gold_dumps.py --all` pour pré-générer les dumps
- Guide complet : `site/_pages/instructor/`
