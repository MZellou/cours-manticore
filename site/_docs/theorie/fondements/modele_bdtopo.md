---
layout: default
title: Modèle BDTOPO
parent: Fondements
nav_order: 2
grand_parent: Théorie
---

# Modèle BDTOPO : comprendre les données du TD

> La BDTOPO est la base de données topographique de l'IGN. Elle contient l'ensemble des objets topographiques du territoire français avec leur géométrie et leur classification.

---

## Vue d'ensemble

| Chiffre | Valeur |
|---------|--------|
| Tables utilisées | 22 |
| Volume total | ~30 Go (Parquet) |
| Routes | 20M+ tronçons |
| Zones d'intérêt | 596k entrées |
| SRID | **Lambert-93 (EPSG:2154)** |

> **Attention** : les coordonnées GPS (WGS84/EPSG:4326) doivent être transformées avec `ST_Transform(geom, 2154)` pour être comparées aux données BDTOPO.

---

## Ontologie : 3 niveaux hiérarchiques

La BDTOPO organise ses objets en une hiérarchie **Database → Object → Detail** :

```
Database: BDTOPO
├── Object: Tronçon de route
│   ├── Detail: Route à 1 chaussée
│   ├── Detail: Route à 2 chaussées
│   ├── Detail: Type autoroutier
│   ├── Detail: Chemin
│   └── Detail: Sentier
├── Object: Construction ponctuelle
│   ├── Detail: Éolienne
│   ├── Detail: Transformateur
│   ├── Detail: Phare
│   └── Detail: Tour de contrôle
└── Object: Zone d'activité ou d'intérêt
    ├── Detail: Hôpital
    ├── Detail: Gendarmerie
    ├── Detail: Zone industrielle
    └── Detail: Barrage
```

### En SQL

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

### En Cypher

```cypher
MATCH path = (d)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy;
```

→ **Même résultat, mais Cypher est plus lisible pour les traversées profondes.**

---

## Tables clés par rôle

### Table maîtresse : `zone_d_activite_ou_d_interet` (596k lignes)

La plus riche. Contient hôpitaux, gendarmeries, zones industrielles, églises, écoles…

Filtres utiles :
- `categorie` : Santé, Administratif ou militaire, Industriel et commercial…
- `nature` : Hôpital, Gendarmerie, Zone industrielle…
- `nature_detaillee` : Place, Port de commerce, École élémentaire…

### Réseau routier : `troncon_de_route` (20M+ lignes)

Chaque tronçon a des attributs de **routage** :

| Attribut | Utilité |
|----------|---------|
| `importance` (1-6) | 1 = national, 5 = local |
| `nature` | Autoroute, Route, Chemin, Sentier |
| `largeur_de_chaussee` | Convois exceptionnels (rôle Énergie) |
| `restriction_de_poids_total` | Poids lourds (rôle Ravitaillement) |
| `vitesse_moyenne_vl` | Calcul de temps de parcours |
| `sens_de_circulation` | Graphe orienté ou non |

### Tables spécialisées

| Table | Rôle principal | Points clés |
|-------|---------------|-------------|
| `aerodrome` | Attaque | `categorie` filtre intérêt |
| `equipement_de_transport` | Attaque/Ravitaillement | Ports, gares, échangeurs |
| `poste_de_transformation` | Énergie | `importance` 1-6 (1 = critique) |
| `ligne_electrique` | Énergie | `voltage` THT 225/400kV |
| `reservoir` | Énergie/Ravitaillement | Réservoirs industriels |
| `construction_ponctuelle` | Tous | Éoliennes, phares, antennes |
| `construction_surfacique` | Défense | Ponts, barrages |

---

## Du tronçon au graphe : le rôle de r2gg

La BDTOPO stocke des **lignes géométriques**, pas un graphe. Pour calculer des itinéraires, il faut transformer ces lignes en **nœuds + arêtes** :

```
BDTOPO (géométrie)          Graphe (topologie)
┌──────────────┐            ┌──────────────┐
│ Tronçon ABC  │   r2gg    │ node_A ─edge─ node_B │
│ (LineString) │ ────────→ │ node_B ─edge─ node_C │
└──────────────┘            └──────────────┘
```

**r2gg** (route-graph-generator) fait cette transformation et alimente **pgRouting**.

Résultat : tables `ways` (arêtes) et `ways_vertices_pgr` (sommets).

> **Dans ce TD** : les graphs sont pré-calculés (Gold Dumps) par l'instructeur. Pas besoin d'installer r2gg.

---

## Centrales nucléaires

Les centrales ne sont **pas** dans la BDTOPO. Elles sont injectées comme POIs custom lors du setup :

```bash
python scripts/00_setup.py --epci "CU de Dunkerque"
# → injecte Gravelines automatiquement
```

Table : `mission_custom_pois` (id, nom, type, puissance_mw, geometrie).

---

## Référence complète

Voir la page [Contenu des données BDTOPO]({% link _docs/theorie/avance/contenu_donnees.md %}) pour le détail complet de chaque table (comptages, nomenclature, filtres par rôle).
