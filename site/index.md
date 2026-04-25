---
layout: default
title: Accueil
---

# Opération Manticore

**Cours BDD NoSQL — Graph + Spatial** | PostGIS + pgRouting + Neo4j

> *Vous êtes agents de renseignement. Cartographiez les infra critiques d'une zone EPCI et évaluez la résilience de son réseau routier.*

---

## 4 rôles par groupe

| | Rôle | Mission |
|--|------|---------|
| ⚔️ | **Attaque** | Identifier les cibles stratégiques (aérodromes, ports, casernes) |
| 🛡️ | **Défense** | Protéger les points vitaux (hôpitaux, ponts, gares) |
| 📦 | **Ravitaillement** | Optimiser les flux logistiques (ports fret, zones industrielles) |
| ⚡ | **Énergie** | Sécuriser le réseau énergétique (postes HT, lignes THT, centrales) |

## 3 phases

| Phase | Mode | Thème |
|-------|------|-------|
| 🔍 Phase 1 — Reconnaissance | Solo (par rôle) | POIs critiques (PostGIS) |
| 🗺️ Phase 2 — Cartographie | Groupe | Routes + graphe (pgRouting + Neo4j) |
| 📊 Phase 3 — Simulation | Groupe | Benchmark SQL vs Cypher |

## Quick start

```bash
git clone <repo> && cd cours-manticore
make setup
python scripts/00_setup.py --epci "<votre EPCI>"
```

→ Lancer avec le [Briefing général](/missions/briefing/)
