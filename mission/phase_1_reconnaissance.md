---
title: Phase 1 — Reconnaissance
---
# Phase 1 — Reconnaissance

> *"Identifier les POIs critiques de votre EPCI selon votre assignation."*

**Mode** : Solo (chaque agent travaille sur son rôle).
**Durée estimée** : 1h30

---

## Prérequis

- Docker stack lancé (PostGIS + Neo4j)
- Données chargées : `python scripts/00_setup.py --epci "<votre EPCI>"`
- Votre briefing rôle dans `mission/roles/<votre_role>.md`

---

## Tâches

### T1 — Explorer l'ontologie BDTOPO

L'ontologie a 3 niveaux hiérarchiques : Database → Object → Detail.

```sql
WITH RECURSIVE hierarchy AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
    FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id
)
SELECT depth, obj_type, name FROM hierarchy ORDER BY depth;
```

**Objectif** : comprendre les relations `parent_id` pour écrire vos requêtes POI.

### T2 — Sélectionner les POIs de votre rôle

Consultez votre briefing rôle (`mission/roles/<votre_role>.md`) pour connaître :
- Les tables BDTOPO à interroger
- Les filtres (nature, catégorie, importance)
- Les jointures spatiales à effectuer

Écrivez vos requêtes et insérez les résultats dans `mission_pois` :

```sql
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'votre_role', 'source_table', cleabs, categorie, nature, toponyme, geom
FROM votre_table
WHERE vos_filtres;
```

### T3 — Ajouter des critères de criticité

Enrichissez vos POIs avec des critères d'importance :
- Postes électriques : `CAST(importance AS INTEGER) <= 3`
- Aérodromes : `categorie IN ('Internationale', 'Nationale')`
- Zones militaires : `categorie = 'Administratif ou militaire'`

### T4 — Clusteriser les POIs (ST_ClusterDBSCAN)

Détectez les grappes tactiques :

```sql
WITH clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid
    FROM mission_pois
)
SELECT cid, COUNT(*) FROM clustered WHERE cid IS NOT NULL GROUP BY cid ORDER BY count DESC;
```

Interprétez : où sont les zones de concentration stratégique ?

### T5 — Partager vos POIs avec votre groupe

En fin de phase 1, les 4 agents fusionnent leurs POIs dans `mission_pois` (table partagée). Chaque rôle a son propre set → la table contient les POIs de tous les rôles du groupe.

---

## Indices Codestral

```
"Écris une requête SQL PostGIS qui trouve tous les hôpitaux et casernes
dans un polygone EPCI (table zone_d_activite_ou_d_interet) en utilisant
ST_Intersects et ST_ClusterDBSCAN pour les grouper en clusters de 2km."
```

```
"Comment utiliser WITH RECURSIVE pour traverser une hiérarchie parent_id
en PostgreSQL ? Montre la syntaxe avec un cas de base et un cas récursif."
```

---

## Critères de validation

- [ ] `SELECT count(*) FROM mission_pois WHERE role = 'votre_role'` → > 0
- [ ] Chaque source de POI identifiée dans le briefing retourne des résultats
- [ ] ST_ClusterDBSCAN détecte au moins 1 cluster
- [ ] Requêtes documentées dans le rapport (avec commentaires)
