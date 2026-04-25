# Opération Manticore — Cours BDD NoSQL (Graph + Spatial)

**Format** : 0.5J théorie + 2J TD
**Stack** : PostGIS + pgRouting + Neo4j + Codestral CLI
**Données** : BDTOPO IGN — 10 EPCIs tactiques
**Calibrage** : 40 étudiants / 10 groupes × 4 rôles

---

## Vue d'ensemble

Projet immersif : équipes d'agents militaires, chaque équipe reçoit **1 EPCI** et travaille en **3 phases connectées**.

| Phase | Intitulé | Mode | Thème |
|-------|----------|------|-------|
| 1 | Reconnaissance | Solo (par rôle) | POIs critiques (PostGIS + WITH RECURSIVE) |
| 2 | Cartographie | Groupe (4 rôles fusionnés) | Routes + graphe (pgRouting + Neo4j/APOC) |
| 3 | Simulation | Groupe | Destruction + résilience (benchmark SQL vs Cypher) |

**4 rôles** : Attaque / Défense / Ravitaillement / Énergie

**Livrables** : carte PNG + rapport markdown + présentation orale 10 min

---

## EPCIs assignés

| # | EPCI | Profil tactique |
|---|------|----------------|
| 1 | Brest Métropole | Port militaire Atlantique |
| 2 | Le Havre Seine Métropole | Port pétrolier estuaire |
| 3 | CU de Dunkerque | Frontière + nucléaire |
| 4 | CA du Cotentin | Péninsule + nucléaire |
| 5 | Grenoble-Alpes-Métropole | Cuvette montagneuse |
| 6 | Eurométropole de Strasbourg | Frontière Allemagne |
| 7 | Métropole Européenne de Lille | Frontière Belgique |
| 8 | CA du Pays Basque | Frontière Espagne + montagne |
| 9 | Métropole Rouen Normandie | Vallée Seine |
| 10 | Bordeaux Métropole | Estuaire Gironde |

---

## Préparation instructeur

### 1. Gold Dumps (routage)

```bash
# Un seul EPCI
python scripts/admin_generate_gold_dumps.py --epci "Brest Métropole"

# Tous les EPCIs
python scripts/admin_generate_gold_dumps.py --all
```

### 2. Slides théorie

```bash
npx @marp-team/marp-cli slides/theorie_bdd_nosql.md -o slides/theorie_bdd_nosql.html
```

### 3. Données BDTOPO

Fichiers Parquet sur le store CIFS :
`/media/stores/cifs/store-DAI/pocs/bd_search/postgis/data/parquet/`

---

## Setup étudiant

### 1. Lancer les bases

```bash
cd cours-manticore
cp .env.example .env
docker compose up -d
uv sync
```

### 2. Installer Codestral CLI

https://console.mistral.ai/codestral/cli

### 3. Charger votre EPCI

```bash
python scripts/00_setup.py --epci "<votre EPCI>"
```

### 4. Lancer les phases

```bash
# Phase 1
python scripts/01_explore_postgis.py --role attaque

# Phase 2
python scripts/02_migrate_to_neo4j.py
python scripts/03_routing_pgrouting.py --role ravitaillement

# Phase 3
python scripts/04_benchmark_comparison.py --role energie --map data/carte_situation.png
```

---

## Structure

```
mission/                  # Énoncés étudiant
  00_briefing.md          # Briefing général + assignation groupes
  phase_1_reconnaissance.md
  phase_2_cartographie.md
  phase_3_simulation.md
  debriefing.md
  roles/                  # Briefings par rôle
    attaque.md
    defense.md
    ravitaillement.md
    energie.md
scripts/                  # Corrigés
  00_setup.py
  01_explore_postgis.py
  02_migrate_to_neo4j.py
  03_routing_pgrouting.py
  04_benchmark_comparison.py
  admin_generate_gold_dumps.py
slides/                   # Théorie Marp
  theorie_bdd_nosql.md
data/                     # Données BDTOPO + Gold Dumps
```
