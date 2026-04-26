---
layout: default
title: Accueil
nav_order: 0
---

# Opération Manticore

**Cours BDD NoSQL — Graph + Spatial** · PostGIS + pgRouting + Neo4j
*0.5J théorie · 2J TD · 40 étudiants / 10 groupes × 4 rôles*

> *Vous êtes agents de renseignement. Cartographiez les infrastructures critiques d'une zone EPCI et évaluez la résilience de son réseau routier face à une simulation d'attaque.*

---

## ▶ Commence ici

1. **[📖 Briefing général]({% link _docs/missions/briefing.md %})** — l'énoncé de la mission, les groupes, les rôles, les livrables.
2. **[🛠 Setup technique]({% link _docs/setup.md %})** — Docker + Python + EPCI assigné.
3. **[🎯 Phase 1 — Reconnaissance]({% link _docs/missions/phase_1_reconnaissance.md %})** — démarre le TD.

> Vous pouvez consulter les **[Corrigés]({% link _docs/corriges.md %})** à tout moment.
> L'objectif est de comprendre, pas de bloquer. Le LLM est votre co-pilote, pas votre béquille.

---

## Ordre de lecture recommandé

```
Briefing général
     │
     ├── Setup (1ère fois)
     │
     ├── Théorie pré-requise → CAP, NoSQL, PostGIS essentiels
     │
     ├── Phase 1 — Reconnaissance (PostGIS, SQL spatial)
     │       ↓
     │   Checkpoint Phase 1
     │       ↓
     ├── Théorie Phase 2 → r2gg, pgRouting, Cypher 5-min
     │       ↓
     ├── Phase 2 — Cartographie (graphe + Neo4j)
     │       ↓
     │   Checkpoint Phase 2
     │       ↓
     ├── Théorie Phase 3 → APOC, lecture de plans
     │       ↓
     └── Phase 3 — Simulation (benchmark + attaque)
             ↓
         Debriefing
```

---

## Les 4 rôles

| | Rôle | Mission |
|--|------|---------|
| ⚔️ | **[Attaque]({% link _docs/roles/attaque.md %})** | Cibles stratégiques (aérodromes, ports, casernes) |
| 🛡️ | **[Défense]({% link _docs/roles/defense.md %})** | Points vitaux (hôpitaux, ponts, gares) |
| 📦 | **[Ravitaillement]({% link _docs/roles/ravitaillement.md %})** | Flux logistiques (ports fret, zones industrielles) |
| ⚡ | **[Énergie]({% link _docs/roles/energie.md %})** | Réseau énergétique (postes HT, lignes THT, centrales) |

## Les 3 phases

| Phase | Mode | Thème | Durée |
|-------|------|-------|-------|
| 🔍 [Phase 1 — Reconnaissance]({% link _docs/missions/phase_1_reconnaissance.md %}) | Solo (par rôle) | POIs critiques (PostGIS) | 4h |
| 🗺️ [Phase 2 — Cartographie]({% link _docs/missions/phase_2_cartographie.md %}) | Groupe | Routes + graphe (pgRouting + Neo4j) | 5h |
| 📊 [Phase 3 — Simulation]({% link _docs/missions/phase_3_simulation.md %}) | Groupe | Benchmark SQL vs Cypher + attaque | 5h |

## Quick start

```bash
git clone <repo> && cd cours-manticore
make setup
python scripts/00_setup.py --epci "<votre EPCI>"
```

→ Continuez avec le **[Briefing général]({% link _docs/missions/briefing.md %})**.
