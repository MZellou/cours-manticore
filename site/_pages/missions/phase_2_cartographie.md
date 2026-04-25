---
layout: default
title: Phase 2 — Cartographie
parent: Missions
nav_order: 3
---

> *"Construire et interroger un graphe de routes pour naviguer vers vos objectifs."*

**Mode** : Groupe (les 4 rôles fusionnent leurs POIs et travaillent sur le même graphe).
**Durée estimée** : 2h

---

## Comprendre : le pivot r2gg, ou comment modéliser un graphe en SQL

La BDTOPO stocke les routes comme des **lignes géométriques** dans une table relationnelle.
Un tronçon de route est une ligne avec des attributs (nature, vitesse, largeur...).
Ce n'est pas un graphe : il n'y a pas de nœuds, pas d'arêtes orientées, pas de coût de traversée.

**r2gg** (route-graph-generator) transforme ces lignes en un **graphe navigable**.
Il le fait en deux étapes :

### Étape 1 : Extraction → Pivot

```
BDTOPO (PostGIS)                      Pivot (schéma normalisé)
┌──────────────────────┐              ┌──────────────────────┐
│ troncon_de_route     │              │ nodes                │
│ ├─ geometrie (line)  │  ──r2gg──>  │ ├─ id, lon, lat, geom│
│ ├─ nature            │   sql2pivot  │ edges                │
│ ├─ vitesse_moyenne   │              │ ├─ source_id → node  │
│ ├─ largeur_chaussee  │              │ ├─ target_id → node  │
│ └─ restriction_*     │              │ ├─ length_m          │
└──────────────────────┘              │ ├─ cost_car, cost_pieton │
                                     │ └─ direction (0/1/-1) │
                                     └──────────────────────┘
```

**Le pivot** n'est rien d'autre qu'un **modèle de graphe** : une table de nœuds (`nodes`) et une table d'arêtes (`edges`) reliées par `source_id`/`target_id`. C'est le schéma classique d'un ** graphe orienté pondéré**, stocké en SQL.

### Étape 2 : Pivot → Moteurs de routage

Le même pivot alimente **plusieurs moteurs** :

```
                    ┌─→ pgRouting   (tables ways + ways_vertices_pgr dans PostGIS)
Pivot (nodes+edges) ├─→ OSRM         (fichiers .osrm)
                    └─→ Valhalla     (tuiles)
```

Chaque moteur réinterprète le même graphe selon ses propres structures.
C'est l'avantage du **pivot** : une seule extraction, plusieurs formats.

### Pourquoi c'est pédagogique ?

| Question | Modèle relationnel (BDTOPO) | Modèle graphe (pivot r2gg) |
|----------|---------------------------|---------------------------|
| "Quels tronçons croisent un polygone ?" | ✅ `ST_Intersects` (PostGIS) | ❌ Pas natif |
| "Quel est le plus court chemin entre A et B ?" | ❌ Il faudrait écrire Dijkstra en SQL pur | ✅ `pgr_dijkstra` |
| "Que se passe-t-il si on coupe une arête ?" | ❌ Pas de notion d'arête | ✅ `cost = -1` → recalcul |
| "Quels sont les voisins du nœud 42 ?" | ❌ Jointure géométrique complexe | ✅ `WHERE source_id = 42 OR target_id = 42` |

> **Leçons** :
> 1. On peut **modéliser un graphe en SQL** (tables nodes/edges), mais l'interrogation des parcours reste limitée.
> 2. r2gg fait ce travail de **transformation linéaire → graphe** automatiquement.
> 3. pgRouting ajoute les **algorithmes** (Dijkstra, A*) qui manquent au SQL pur.
> 4. Mais pour l'**ontologie** (hiérarchies profondes), Neo4j restera plus naturel que SQL récursif.

---

## Prérequis

- Phase 1 terminée : `mission_pois` contient les POIs des 4 rôles
- Gold Dumps r2gg chargés (tables `ways` + `ways_vertices_pgr` dans PostGIS)
  - Générés par l'instructeur : `python scripts/admin_generate_gold_dumps.py --epci "<EPCI>"`

---

## Tâches

### T1 — Explorer le graphe généré par r2gg

r2gg a transformé la BDTOPO en graphe. Observez sa structure :

```sql
-- Les arêtes (routes transformées en arêtes pondérées)
SELECT id, source, target, cost, reverse_cost, length_m
FROM ways LIMIT 10;

-- Les sommets (intersections de routes)
SELECT id, ST_X(geom) AS lon, ST_Y(geom) AS lat
FROM ways_vertices_pgr LIMIT 10;

-- Combien de nœuds et d'arêtes dans votre graphe ?
SELECT
    (SELECT count(*) FROM ways) AS nb_arretes,
    (SELECT count(*) FROM ways_vertices_pgr) AS nb_noeuds;
```

**Question** : comparez `nb_arretes` avec le nombre de tronçons dans `troncon_de_route`.
Pourquoi sont-ils différents ? (indice : r2gg découpe les tronçons aux intersections pour créer des arêtes atomiques).

### T2 — Associer les POIs aux sommets du graphe

Les POIs sont des points géométriques, pas des nœuds du graphe.
Il faut les "snapper" au sommet le plus proche :

```sql
-- Trouver le sommet du graphe le plus proche de chaque POI
SELECT p.nom, p.role,
       v.id AS vertex_id,
       ST_Distance(p.geom, v.geom) AS distance_snap
FROM mission_pois p
CROSS JOIN LATERAL (
    SELECT id, geom FROM ways_vertices_pgr
    ORDER BY geom <-> p.geom LIMIT 1
) v
ORDER BY distance_snap DESC LIMIT 10;
```

Pourquoi les POIs éloignés des routes ont-ils un `distance_snap` élevé ?
Est-ce un problème pour le routage ?

### T3 — Calculer des itinéraires (Dijkstra)

Maintenant que le graphe existe, calculez le plus court chemin entre 2 POIs :

```sql
SELECT seq, node, edge, cost, agg_cost
FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM ways',
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'attaque' LIMIT 1),
    (SELECT v.id FROM mission_pois p, LATERAL (
        SELECT id FROM ways_vertices_pgr ORDER BY geom <-> p.geom LIMIT 1
    ) v WHERE p.role = 'defense' LIMIT 1),
    directed := false
);
```

Essayez plusieurs paires de rôles (attaque→énergie, ravitaillement→défense...).

### T4 — Routage contraint par rôle

Le coût dans le graphe n'est pas fixe — il dépend du **profil** du véhicule.
r2gg génère plusieurs colonnes de coût (`cost_car`, `cost_pedestrian`...).
Mais on peut aussi les **recalculer dynamiquement** :

| Rôle | Profil | Clause SQL |
|------|--------|------------|
| **Ravitaillement** | Poids lourds | `CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE cost END` |
| **Énergie** | Convois exceptionnels | `CASE WHEN largeur_de_chaussee < 4 THEN -1 ELSE cost END` |
| **Attaque** | Discrétion (chemins) | `CASE WHEN nature IN ('Chemin','Sentier') THEN cost*0.7 ELSE cost*1.3 END` |
| **Défense** | Rapidité (grandes routes) | `CASE WHEN importance >= 3 THEN cost*0.5 ELSE cost END` |

```sql
-- Ravitaillement : bloquer les routes interdites aux poids lourds
SELECT max(agg_cost) FROM pgr_dijkstra(
    'SELECT id, source, target,
            CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE cost END AS cost,
            CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE reverse_cost END AS reverse_cost
     FROM ways',
    source_vertex, target_vertex, directed := false
);
```

Comparez avec le chemin "normal". Quel est le détour imposé par la contrainte ?

### T5 — Migrer dans Neo4j et combiner graphe routier + ontologie

Le graphe r2gg est en SQL. L'ontologie BDTOPO est dans Neo4j.
La phase 2 consiste à **connecter les deux mondes** :

```bash
python scripts/02_migrate_to_neo4j.py
```

Dans Neo4j Browser :

```cypher
-- Vérifier les POIs chargés
MATCH (p:POI) RETURN p.role, count(*) ORDER BY count DESC;

-- Trouver les sous-types d'un objet (traversée ontologique)
MATCH path = (d:Detail)-[:EST_SOUS_TYPE_DE*]->(o:Object {name: 'Tronçon de route'})
RETURN [n IN nodes(path) | n.name] AS hierarchy LIMIT 5;

-- Chemin le plus court entre POIs (si distances chargées)
MATCH (a:POI), (b:POI) WHERE id(a) < id(b)
CALL apoc.algo.dijkstra(a, b, 'DISTANCE', 'meters')
YIELD path, weight
RETURN a.nom, b.nom, weight AS distance_m
ORDER BY weight DESC LIMIT 10
```

### T6 — Réflexion : SQL vs Graphe vs Les deux

| Tâche | Quel outil ? | Pourquoi ? |
|-------|-------------|------------|
| Trouver les hôpitaux dans un polygone EPCI | PostGIS (SQL) | `ST_Intersects` est natif |
| Trouver le plus court chemin entre 2 points | pgRouting (graphe dans SQL) | Dijkstra nécessite un graphe |
| Explorer une hiérarchie de types sur 3 niveaux | Neo4j (Cypher) | `[:EST_SOUS_TYPE_DE*]` vs `WITH RECURSIVE` |
| Mapper un POI au sommet le plus proche | PostGIS (SQL) | `ORDER BY geom <-> poi.geom` |
| Trouver tous les chemins entre 2 nœuds d'ontologie | Neo4j (Cypher) | `allShortestPaths` natif |

> **Conclusion** : dans la vraie vie, on combine SQL (géométrie, filtres) et graphe (parcours, routage). Aucun des deux n'est suffisant seul.

---

## Indices Codestral

```
"Explique comment r2gg (route-graph-generator) transforme des tronçons
de route BDTOPO en un graphe navigable. Décris le schéma pivot
(nodes + edges) et pourquoi ce modèle est nécessaire pour le routage."
```

```
"Écris une requête pgRouting pgr_dijkstra avec un coût dynamique :
si la route a une restriction de poids, le coût est -1 (bloqué).
Montre comment passer ce coût personnalisé dans la sous-requête SQL."
```

---

## Critères de validation

- [ ] `SELECT count(*) FROM ways` et `ways_vertices_pgr` → graphe non vide
- [ ] Snap des POIs aux sommets : chaque POI a un `vertex_id`
- [ ] Dijkstra retourne un chemin valide entre 2 POIs de rôles différents
- [ ] Le routage contraint montre une différence mesurable vs le routage normal
- [ ] Neo4j contient les POIs des 4 rôles + requêtes Cypher fonctionnelles
- [ ] Le tableau comparatif SQL vs Graphe est complété dans le rapport
