---
title: Briefing général
layout: default
---
# OPÉRATION MANTICORE — Briefing Général

> **Vous êtes agents de renseignement. Votre mission : cartographier les infrastructures critiques d'une zone EPCI et évaluer la résilience de son réseau routier face à une simulation d'attaque.**

## Composition (40 étudiants / 10 groupes × 4 agents)

| Groupe | EPCI assigné | Profil tactique |
|--------|-------------|-----------------|
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

### Rôles (4 par groupe)

Chaque membre du groupe adopte un rôle spécifique :

| Badge | Rôle | Objectif |
|-------|------|---------|
| ⚔️ | **ATTAQUE** | Identifier les cibles stratégiques (aérodromes, ports, casernes) |
| 🛡️ | **DÉFENSE** | Identifier les points à protéger (hôpitaux, ponts, gares) |
| 📦 | **RAVITAILLEMENT** | Optimiser les flux logistiques (ports fret, zones industrielles) |
| ⚡ | **ÉNERGIE** | Sécuriser le réseau énergétique (postes HT, lignes THT, centrales) |

## 3 phases de la mission

| Phase | Intitulé | Solo/Groupe | Livrable |
|-------|----------|-------------|----------|
| 🔍 Phase 1 | Reconnaissance | Solo (par rôle) | Requêtes SQL + table `mission_pois` |
| 🗺️ Phase 2 | Cartographie | Groupe (4 rôles fusionnés) | Graphe Neo4j + routes pgRouting |
| 📊 Phase 3 | Simulation | Groupe | Benchmark SQL/Cypher + carte PNG |

## Prérequis

1. Installer [Codestral CLI](https://console.mistral.ai/codestral/cli) : votre assistant de codage IA
2. Cloner le repo et lancer `docker compose up -d && uv sync`
3. Charger votre EPCI : `python scripts/00_setup.py --epci "<votre EPCI>"`

## Livrable final (par groupe)

- **Carte PNG** : situation tactique consolidée (4 rôles superposés)
- **Rapport markdown** : analyse critique (2-3 pages)
- **Présentation orale** : 10 min (structure libre, mappez vos résultats)
