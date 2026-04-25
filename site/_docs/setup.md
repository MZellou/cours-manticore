---
layout: default
title: Environnement
nav_order: 5
---

# Environnement de travail

> PostGIS (avec pgRouting) + Neo4j + Python. Tout tourne en local via Docker.

---

## 1. Prérequis

| Outil | Version | Vérification |
|-------|---------|-------------|
| **Docker** | 20+ | `docker --version` |
| **Docker Compose** | v2+ | `docker compose version` |
| **Python** | 3.11+ | `python --version` |
| **uv** | latest | `uv --version` ([installer](https://docs.astral.sh/uv/)) |
| **Git** | 2.x | `git --version` |

## 2. Installation

```bash
# Cloner le repo
git clone <repo-url> && cd cours-manticore

# Configurer les variables d'environnement
cp .env.example .env

# Lancer les conteneurs (PostGIS + Neo4j)
docker compose up -d

# Installer les dépendances Python
uv sync
```

## 3. Vérifications

### PostGIS + pgRouting

```bash
docker exec -it manticore-postgis psql -U postgres -d bdtopo_manticore
```

```sql
-- Extensions actives ?
SELECT extname FROM pg_extension WHERE extname IN ('postgis', 'pgrouting');
-- Attendu : postgis, pgrouting

-- Version PostGIS ?
SELECT PostGIS_Version();
```

### Neo4j + APOC

Ouvrir [http://localhost:7474](http://localhost:7474) (login : `neo4j` / `manticore2026`).

```cypher
// Vérifier qu'APOC est installé
RETURN apoc.version();
```

### Données EPCI

```bash
# Lister les EPCIs disponibles
python scripts/00_setup.py --list-epci

# Charger votre EPCI (remplacer par le nom du groupe)
python scripts/00_setup.py --epci "Brest Métropole"
```

## 4. Architecture des services

```
┌─────────────────────────────────────────┐
│  PostGIS (localhost:5432)                │
│  ├── Extension PostGIS (géométries)     │
│  ├── Extension pgRouting (routage)      │
│  ├── Tables BDTOPO (22 tables)          │
│  ├── bdtopo_ontology (hiérarchie)       │
│  ├── mission_pois (vos POIs)            │
│  └── ways / ways_vertices_pgr (graphe)  │
├─────────────────────────────────────────┤
│  Neo4j (localhost:7474 / 7687)          │
│  ├── Plugin APOC (algorithmes)          │
│  ├── :ClasseOntologie (3 niveaux)       │
│  ├── :POI (points d'intérêt)           │
│  └── [:DISTANCE] / [:EST_SOUS_TYPE_DE] │
└─────────────────────────────────────────┘
```

## 5. Problèmes fréquents

| Problème | Solution |
|----------|----------|
| `Connection refused` (PostGIS) | `docker compose up -d` puis attendre le healthcheck |
| Neo4j ne démarre pas | Vérifier la RAM dispo → réduire `NEO4J_server_memory_heap_max__size` à `512M` |
| `module psycopg2 not found` | `uv sync` dans le dossier du projet |
| `EPCI non trouvé` | Utiliser `--list-epci` pour voir les noms exacts |
| Port 5432 déjà utilisé | Changer `POSTGIS_PORT` dans `.env` |
