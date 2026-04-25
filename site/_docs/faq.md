---
layout: default
title: FAQ & Troubleshooting
nav_order: 7
---

# FAQ & Troubleshooting

> Les problèmes les plus fréquents et leurs solutions.

---

## Installation & Docker

### `docker compose up -d` échoue

```bash
# Vérifier que Docker tourne
docker info

# Vérifier les ports occupés
ss -tlnp | grep -E '5432|7474|7687'

# Forcer le rebuild
docker compose down -v && docker compose up -d --build
```

### Port 5432 déjà utilisé

Un PostgreSQL local tourne déjà. Solution :

```bash
# Option 1 : arrêter le PostgreSQL local
sudo systemctl stop postgresql

# Option 2 : changer le port dans .env
echo "POSTGIS_PORT=5433" >> .env
```

### Neo4j met trop de temps à démarrer

Réduire la heap si < 8 Go de RAM :

```yaml
# docker-compose.yml
NEO4J_server_memory_heap_max__size: 512M  # au lieu de 1G
```

### `uv sync` échoue

```bash
# Vérifier la version Python
python --version  # besoin de 3.11+

# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## PostGIS

### `relation "xxx" does not exist`

Le setup n'a pas été lancé ou l'EPCI n'a pas été chargé :

```bash
python scripts/00_setup.py --list-epci    # vérifier le nom exact
python scripts/00_setup.py --epci "Brest Métropole"  # charger
```

### `function st_intersects does not exist`

L'extension PostGIS n'est pas active :

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Les coordonnées ne matchent pas

BDTOPO utilise **Lambert-93 (EPSG:2154)**. Si vous avez des coordonnées GPS :

```sql
-- Transformer du GPS (4326) vers Lambert-93 (2154)
ST_Transform(ST_SetSRID(ST_MakePoint(lon, lat), 4326), 2154)
```

### `importance` ne filtre pas correctement

La colonne `importance` est un **VARCHAR**, pas un INTEGER :

```sql
-- WRONG
SELECT * FROM poste_de_transformation WHERE importance <= 3;

-- CORRECT
SELECT * FROM poste_de_transformation WHERE CAST(importance AS INTEGER) <= 3;
```

---

## Neo4j

### `Neo4j is not available`

```bash
# Vérifier le conteneur
docker logs manticore-neo4j --tail 20

# Attendre le healthcheck
docker compose ps  # STATUS = "healthy"
```

### Les POIs ne sont pas dans Neo4j

La migration n'a pas été lancée :

```bash
# D'abord charger dans PostGIS (Phase 1)
python scripts/01_explore_postgis.py --role attaque

# Ensuite migrer vers Neo4j
python scripts/02_migrate_to_neo4j.py
```

### `apoc.algo.betweenness` ne fonctionne pas

Vérifier qu'APOC est installé :

```cypher
RETURN apoc.version();
```

Si absent, vérifier dans `docker-compose.yml` :

```yaml
NEO4J_PLUGINS: '["apoc"]'
```

Puis restart : `docker compose restart neo4j`.

---

## Scripts Python

### `module not found: psycopg2`

```bash
uv sync  # installe les dépendances
```

### `No EPCI found matching "xxx"`

Les noms doivent correspondre exactement :

```bash
python scripts/00_setup.py --list-epci  # voir les noms exacts
```

### Le script `01_explore` retourne 0 résultats

Vérifier que les données sont chargées :

```sql
SELECT count(*) FROM zone_d_activite_ou_d_interet;
SELECT count(*) FROM mission_pois;
```

Si vide → relancer `00_setup.py`.

---

## Pour l'instructeur

### Gold Dumps manquants (tables `ways` vides)

Les graphs r2gg doivent être pré-générés :

```bash
python scripts/admin_generate_gold_dumps.py --all
# ou pour un EPCI :
python scripts/admin_generate_gold_dumps.py --epci "Brest Métropole"
```

### EPCIs trop grands (timeout pgRouting)

Éviter Grand Paris (356k routes). Sweet spot : 30k-140k routes.
Voir le détail dans [Contenu des données]({% link _docs/theorie/contenu_donnees.md %}#5-points-dattention-pour-le-td).
