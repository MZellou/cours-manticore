---
layout: default
title: Accueil
---

# Opération Manticore

**Cours BDD NoSQL — Graph + Spatial** | PostGIS + pgRouting + Neo4j

> *Vous êtes agents de renseignement. Votre mission : cartographier les infrastructures critiques d'une zone EPCI et évaluer la résilience de son réseau routier face à une simulation d'attaque.*

## Format

- **0.5J** théorie + **2J** TD
- **40 étudiants** / 10 groupes × 4 rôles
- **Stack** : PostGIS + pgRouting + Neo4j + Codestral CLI

## 3 phases

| Phase | Mode | Thème |
|-------|------|-------|
| 1 — Reconnaissance | Solo (par rôle) | POIs critiques (PostGIS) |
| 2 — Cartographie | Groupe | Routes + graphe (pgRouting + Neo4j) |
| 3 — Simulation | Groupe | Benchmark SQL vs Cypher |

## Quick start

```bash
git clone <repo> && cd cours-manticore
make setup                    # clone submodules + pull data + docker + uv
python scripts/00_setup.py --epci "<votre EPCI>"
```

→ Lire le [Briefing général](/missions/briefing/) pour la suite.
