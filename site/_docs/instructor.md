---
layout: default
title: Instructeur
nav_order: 9
---

# Guide instructeur

> Tout ce que l'instructeur doit préparer avant la session.

---

## 1. Checklist pré-cours

- [ ] **Docker stack** : `docker compose up -d` → les 2 conteneurs sont `healthy`
- [ ] **Gold Dumps** : générés pour les 10 EPCIs (`python scripts/admin_generate_gold_dumps.py --all`)
- [ ] **Pages théorie** : passer en revue `_docs/theorie/*.md` (servent de support pour la 0.5J théorie)
- [ ] **Neo4j heap** : adapté aux laptops étudiants (512M si < 8 Go RAM)
- [ ] **Données Parquet** : accessibles sur le partage CIFS ou en local
- [ ] **`.env`** : distribué aux étudiants (copie de `.env.example`)

## 2. Assignation groupes × EPCI

| Groupe | EPCI | Profil tactique |
|--------|------|-----------------|
| 1 | Brest Métropole | Port militaire Atlantique |
| 2 | Le Havre Seine Métropole | Port pétrolier estuaire |
| 3 | CU de Dunkerque | Frontière + nucléaire (Gravelines) |
| 4 | CA du Cotentin | Péninsule + nucléaire (Flamanville) |
| 5 | Grenoble-Alpes-Métropole | Cuvette montagneuse |
| 6 | Eurométropole de Strasbourg | Frontière Allemagne |
| 7 | Métropole Européenne de Lille | Frontière Belgique |
| 8 | CA du Pays Basque | Frontière Espagne + montagne |
| 9 | Métropole Rouen Normandie | Vallée Seine |
| 10 | Bordeaux Métropole | Estuaire Gironde |

Chaque groupe de 4 étudiants : 1 Attaque, 1 Défense, 1 Ravitaillement, 1 Énergie.

## 3. Timing suggéré (2.5 jours)

| Moment | Durée | Activité |
|--------|-------|----------|
| **J1 matin** | 3h | Cours magistral (pages [Théorie]({% link _docs/theorie.md %}) projetées) + installation |
| **J1 après-midi** | 3h | Phase 1 : Reconnaissance (solo) |
| **J2 matin** | 3h | Phase 2 : Cartographie (groupe) |
| **J2 après-midi** | 3h | Phase 3 : Simulation + benchmark |
| **J3 matin** | 2h | Présentations orales + debriefing |

## 4. Points de blocage fréquents

| Problème | Solution |
|----------|----------|
| **Mémoire Neo4j** | Réduire heap à `512M` dans `docker-compose.yml` |
| **SRID mix** | BDTOPO = 2154. Rappeler `ST_Transform` pour les coords GPS |
| **`importance` VARCHAR** | Toujours `CAST(importance AS INTEGER)` pour les filtres |
| **Cypher lent** | Créer les index avant migration : `CREATE INDEX FOR (p:POI) ON (p.role)` |
| **EPCI trop grand** | Grand Paris = timeout pgRouting. Sweet spot : 30k-140k routes |
| **Centrales nucléaires** | Injectées par `00_setup.py` → table `mission_custom_pois` |
| **r2gg non installé** | Utiliser les Gold Dumps pré-générés |

## 5. Centrales nucléaires (custom POIs)

Injectées automatiquement par `00_setup.py` pour les EPCIs proches :

| Centrale | Coords approx. | EPCI concerné |
|----------|----------------|---------------|
| Gravelines | (2.14, 51.0) | CU de Dunkerque |
| Flamanville | (-1.85, 49.55) | CA du Cotentin |
| Cattenom | (6.25, 49.42) | CC de Cattenom et Environs |
| Chooz | (4.82, 50.08) | Ardenne Métropole |
| Civaux | (0.65, 46.45) | CU du Grand Poitiers |

Table : `mission_custom_pois` (id, nom, type, puissance_mw, geometrie).

## 6. Corrigés

Les scripts `01_explore_postgis.py` à `04_benchmark_comparison.py` contiennent les **corrigés complets**.

Pour distribuer aux étudiants :
- Fournir les briefings dans `mission/` (déjà présents)
- Les scripts sont des exemples — les étudiants écrivent leurs propres requêtes dans un notebook ou en CLI

## 7. Évaluation

Voir la [grille d'évaluation]({% link _docs/missions/debriefing.md %}#grille-dévaluation) :
- Requêtes SQL : **25%**
- Requêtes Cypher : **20%**
- Routage pgRouting : **20%**
- Benchmark : **15%**
- Carte + rapport : **15%**
- Présentation : **5%**

## 8. Dépannage avancé

### Réinitialiser complètement

```bash
docker compose down -v   # supprime les volumes
docker compose up -d     # recréé les conteneurs
python scripts/00_setup.py --epci "<EPCI>"  # recharge les données
```

### Vérifier les données chargées

```sql
-- Tables BDTOPO chargées
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Comptages par table
SELECT 'mission_pois' AS t, count(*) FROM mission_pois
UNION ALL SELECT 'ways', count(*) FROM ways
UNION ALL SELECT 'bdtopo_ontology', count(*) FROM bdtopo_ontology;
```

### Neo4j : vérifier la migration

```cypher
// Compter les nœuds par label
MATCH (n) RETURN labels(n)[0] AS label, count(*) ORDER BY count DESC;

// Vérifier les relations
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) ORDER BY count DESC;
```
