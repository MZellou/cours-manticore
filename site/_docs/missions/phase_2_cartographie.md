---
title: Phase 2 — Cartographie
parent: Missions
nav_order: 5
layout: default
---
# Phase 2 — Cartographie

> *"Construire et interroger un graphe de routes pour naviguer vers vos objectifs."*

**Mode** : Groupe (les 4 rôles fusionnent leurs POIs et travaillent sur le même graphe).
**Durée estimée** : 5h (tâches principales 2h + Cypher approfondi 1h + pgRouting avancé 1h + réflexion 1h)

<div class="prereq-theorie" markdown="1">
📚 **Théorie pré-requise** — à parcourir avant cette phase

- [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) — *pourquoi* on pivote en graphe (essentiel)
- [Cypher en 5 minutes]({% link _docs/theorie/cypher_5min.md %}) — `MATCH`, `WHERE`, `MERGE`, patterns
- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — index-free adjacency, LPG

**Pré-requis Phase 1** : la table `mission_pois` est non-vide pour les 4 rôles ([Checkpoint Phase 1]({% link _docs/missions/checkpoint_phase_1.md %})).
</div>

[← Transition Phase 1 → Phase 2]({% link _docs/missions/transition_1_2.md %}) — *à lire d'abord pour comprendre ce qui change.*

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
│ ├─ largeur_de_chaussee  │              │ ├─ target_id → node  │
│ └─ restriction_*     │              │ ├─ length_m          │
└──────────────────────┘              │ ├─ cost_car, cost_pieton │
                                      │ └─ direction (0/1/-1) │
                                      └──────────────────────┘
```

**Le pivot** n'est rien d'autre qu'un **modèle de graphe** : une table de nœuds (`nodes`) et une table d'arêtes (`edges`) reliées par `source_id`/`target_id`. C'est le schéma classique d'un **graphe orienté pondéré**, stocké en SQL.

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

## Tâches principales (2h)

### T1 — Explorer le graphe généré par r2gg

r2gg a transformé la BDTOPO en graphe. Observez sa structure :

**Objectifs** :
1. Explorer les tables `ways` et `ways_vertices_pgr`
2. Compter les arêtes et les nœuds
3. Comparer avec le nombre de tronçons dans `troncon_de_route`

**Question** : pourquoi le nombre d'arêtes est-il différent du nombre de tronçons ?
*Indice : r2gg découpe les tronçons aux intersections.*

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t1--explorer-le-graphe-r2gg)

### T2 — Associer les POIs aux sommets du graphe

Les POIs sont des points géométriques, pas des nœuds du graphe.
Il faut les "snapper" au sommet le plus proche.

**Objectif** : trouver le sommet le plus proche de chaque POI.
*Indice : `CROSS JOIN LATERAL` + `ORDER BY geom <-> p.geom LIMIT 1`.*

Pourquoi les POIs éloignés des routes ont-ils un `distance_snap` élevé ? Est-ce un problème ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t2--associer-les-pois-aux-sommets)

<div class="reflexion" markdown="1">
🧠 **Réflexion guidée — dialogue avec le LLM**

**Questions à creuser**
- Pourquoi utiliser `<->` (KNN) plutôt que `ORDER BY ST_Distance(...)` ? Lequel utilise l'index GIST ?
- Que faire d'un POI dont le `dist_snap` dépasse 500 m ? Le filtrer ? Le garder mais le marquer ?
- Si deux POIs sont snappés au **même** sommet, est-ce un problème pour le routage ? Pour la sémantique ?

**Prompts LLM suggérés**
- *"Explique `CROSS JOIN LATERAL` en PostgreSQL avec un cas concret : pour chaque ligne de la table A, trouver le voisin le plus proche dans la table B."*
- *"Quelle est la différence entre l'opérateur `<->` (KNN) et `ST_Distance` côté plan d'exécution ?"*

**Mini-défi**
- Calcule la **distribution** des `dist_snap` (min, médiane, p95, max). Y a-t-il des outliers ?
- Bonus : tracer l'histogramme des distances de snap pour ton rôle.
</div>

### T3 — Calculer des itinéraires (Dijkstra)

Maintenant que le graphe existe, calculez le plus court chemin entre 2 POIs.

**Objectif** : utiliser `pgr_dijkstra` entre un POI attaque et un POI défense.
*Indice : sous-requêtes pour les vertex_ids + `directed := false`.*

Essayez plusieurs paires de rôles (attaque→énergie, ravitaillement→défense...).

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t3--calculer-des-itinraires-dijkstra)

### T4 — Routage contraint par rôle

Le coût dans le graphe n'est pas fixe — il dépend du **profil** du véhicule.

| Rôle | Profil | Clause SQL |
|------|--------|------------|
| **Ravitaillement** | Poids lourds | `CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE cost END` |
| **Énergie** | Convois exceptionnels | `CASE WHEN largeur_de_chaussee < 4 THEN -1 ELSE cost END` |
| **Attaque** | Discrétion (chemins) | `CASE WHEN nature IN ('Chemin','Sentier') THEN cost*0.7 ELSE cost*1.3 END` |
| **Défense** | Rapidité (grandes routes) | `CASE WHEN importance >= 3 THEN cost*0.5 ELSE cost END` |

**Objectif** : recalculer un itinéraire avec votre contrainte de rôle. Comparez avec le chemin "normal".

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t4--routage-contraint-par-rle)

<div class="reflexion" markdown="1">
🧠 **Réflexion guidée — dialogue avec le LLM**

**Questions à creuser**
- Pourquoi la convention pgRouting est `cost = -1` pour "interdit" et pas `NULL` ou `+infinity` ?
- Si on multiplie un coût par 0.7 (raccourcir un chemin), Dijkstra reste-t-il **correct** ? Et avec un coût négatif ?
- Comparer : route "rapidité" (Défense, autoroutes prioritaires) vs route "discrétion" (Attaque, sentiers prioritaires). Combien de % de différence en distance ? En temps ?

**Prompts LLM suggérés**
- *"Pourquoi Dijkstra ne fonctionne pas avec des coûts négatifs ? Quel algo utiliser à la place (Bellman-Ford) ?"*
- *"Écris une sous-requête pgRouting où le coût est dynamique : `cost = base_cost * 0.5` si la route est une autoroute (importance ≤ 2), sinon `cost = base_cost`."*

**Mini-défi**
- Compare la **longueur** et le **temps** du même trajet pour 2 profils différents (par ex. `largeur < 4` vs `cost normal`). Tableau dans le rapport.
- Bonus : combiner 2 contraintes (poids + largeur) en un seul `CASE`.
</div>

### T5 — Migrer dans Neo4j et combiner graphe routier + ontologie

Le graphe r2gg est en SQL. L'ontologie BDTOPO est dans Neo4j.
La phase 2 consiste à **connecter les deux mondes** :

```bash
python scripts/02_migrate_to_neo4j.py
```

**Objectifs dans Neo4j Browser** :
1. Vérifier les POIs chargés (`MATCH (p:POI)`)
2. Traverser l'ontologie (`[:EST_SOUS_TYPE_DE*]`)
3. Calculer un plus court chemin entre POIs (`apoc.algo.dijkstra`)

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t5--migrer-dans-neo4j)

<div class="reflexion" markdown="1">
🧠 **Réflexion guidée — dialogue avec le LLM**

**Questions à creuser**
- Pourquoi crée-t-on des **index** Neo4j *avant* de lancer un gros `MERGE` ? Que se passe-t-il sans index sur 10 000 POIs ?
- `MERGE` vs `CREATE` : pourquoi est-ce que `MERGE` est **idempotent** mais plus lent ? Quand préférer chacun ?
- L'ontologie est-elle un **arbre** ou un **graphe** ? Y a-t-il des cas où un Detail a 2 parents ?

**Prompts LLM suggérés**
- *"Explique l'effet d'un index Neo4j `CREATE INDEX FOR (p:POI) ON (p.cleabs)` sur la vitesse d'un MERGE qui matche par `cleabs`."*
- *"Compare `MERGE` Cypher et `INSERT ... ON CONFLICT DO NOTHING` PostgreSQL. Différences et points communs."*

**Mini-défi**
- Avant migration : compte les nœuds par label (`MATCH (n) RETURN labels(n)[0], count(*)`). Note les chiffres.
- Après migration : recompte. Tout colle ? Si non, pourquoi ?
- Bonus : ajoute un index secondaire sur `(p:POI) ON (p.role)` et `PROFILE` une requête filtrée par rôle avant/après.
</div>

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

## Cypher approfondi (1h)

> Maintenant que les données sont dans Neo4j, allez plus loin que les requêtes de base.

### T7 — Créer des nœuds personnalisés (CREATE / MERGE)

Votre groupe a des **bases avancées** et des **points de ralliement** qui ne sont pas dans la BDTOPO. Créez-les.

**Objectifs** :
1. Créer au moins 2 nœuds `:Base` (base avancée, hôpital de campagne, dépôt...)
2. Les relier aux POIs proches avec des relations `[:DISTANCE]`

*Indice : `CREATE (b:Base {...})`, puis `MATCH (b:Base), (p:POI) WHERE distance(...) < 10000 MERGE (b)-[r:DISTANCE {meters: ...}]->(p)`*

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t7--crer-des-nuds-personnaliss-create--merge)

### T8 — OPTIONAL MATCH et UNWIND

**Objectifs** :
1. Trouver les POIs sans connexion (isolés dans le graphe)
2. Lister les POIs avec leur nombre de voisins (`OPTIONAL MATCH`)
3. Utiliser `UNWIND` pour aplatir les listes

**Exercice** : combien de POIs sont "isolés" (0 voisins dans le graphe Neo4j) ? Pourquoi ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t8--optional-match-et-unwind)

### T9 — Pattern matching avancé

**Objectifs** :
1. Trouver les chemins entre attaque et défense passant **uniquement** par des POIs énergie
2. Détecter les triangles (3 POIs mutuellement connectés)

**Défi** : écrivez une requête Cypher qui trouve le chemin le plus court entre un POI attaque et un POI défense, **en évitant** tous les POIs énergie.
*Indice : `WHERE NOT ... IN` ou `WHERE ALL(n IN nodes(path) WHERE ...)`*

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t9--pattern-matching-avanc)

---

## pgRouting avancé (1h)

### T10 — Matrice de distances entre POIs

**Objectif** : calculer les distances de **chaque source vers chaque cible** en un seul appel.
*Indice : `pgr_dijkstraCostMatrix` + `array_agg(vid)`.*

**Exercice** : calculez la matrice pour votre rôle. Quel est le POI le plus éloigné des autres ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t10--matrice-de-distances)

### T11 — Isochrones (zone accessible en X minutes)

Une isochrone montre la zone atteignable en un temps donné depuis un point.

**Objectif** : trouver tous les sommets atteignables en moins de 10 minutes (cost = secondes).
*Indice : `pgr_dijkstra` avec `WHERE agg_cost <= 600`.*

**Exercice** : tracez les isochrones à 5 min, 10 min, 15 min depuis le POI défense le plus important.

> **Bonus cartographie** : les sommets atteignables peuvent être convertis en polygone (convex hull) pour affichage sur la carte.

→ [Corrigé]({% link _docs/corriges/corrige_phase_2.md %}#t11--isochrones)

---

## Réflexion de groupe (1h)

### T12 — Débat : "Quel outil pour quelle question ?"

En groupe, complétez ce tableau pour **votre EPCI** avec vos mesures réelles :

| Question | SQL ? | Cypher ? |pgRouting ? | Temps (ms) | LOC | Résultat |
|----------|-------|----------|-------------|------------|-----|----------|
| Top 5 POIs par nombre de voisins | | | | | | |
| Chemin le plus court A→B via C | | | | | | |
| POIs isolés (0 connexion) | | | | | | |
| Zone atteignable en 10 min | | | | | | |
| Hiérarchie ontologique complète | | | | | | |

**Débattez** :
1. Y a-t-il des requêtes où SQL est clairement meilleur ?
2. Y a-t-il des requêtes impossibles dans un des outils ?
3. Si vous deviez choisir **un seul** outil pour tout faire, lequel ?

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

```
"Écris une requête Cypher qui utilise OPTIONAL MATCH pour trouver
les POIs qui n'ont pas de voisins dans un graphe de distances.
Puis utilise UNWIND pour lister les noms par rôle."
```

---

## Critères de validation

- [ ] `SELECT count(*) FROM ways` et `ways_vertices_pgr` → graphe non vide
- [ ] Snap des POIs aux sommets : chaque POI a un `vertex_id`
- [ ] Dijkstra retourne un chemin valide entre 2 POIs de rôles différents
- [ ] Le routage contraint montre une différence mesurable vs le routage normal
- [ ] Neo4j contient les POIs des 4 rôles + requêtes Cypher fonctionnelles
- [ ] T7 : au moins 2 nœuds personnalisés créés dans Neo4j
- [ ] T8 : nombre de POIs isolés identifié
- [ ] T10 : matrice de distances calculée pour au moins 1 rôle
- [ ] T11 : isochrone calculée (nombre de sommets atteignables)
- [ ] T12 : tableau comparatif complété avec mesures réelles

<div class="checkpoint" markdown="1">
✅ **Checkpoint avant Phase 3**

Avant la simulation, validez l'état du graphe et de Neo4j :

→ [Checkpoint Phase 2]({% link _docs/missions/checkpoint_phase_2.md %}) — sanity check graphe + Neo4j.
</div>

## Auto-évaluation (non notée)

Cocher ce que vous savez **expliquer à un coéquipier** :

- [ ] Pourquoi r2gg découpe les tronçons aux intersections (lien avec le graphe)
- [ ] Différence `cost` / `reverse_cost`, et convention `-1` = interdit
- [ ] Comment "snapper" un point quelconque au sommet le plus proche (`<->`)
- [ ] Différence `MERGE` vs `CREATE` en Cypher
- [ ] Pourquoi un index Neo4j accélère drastiquement un `MERGE`
- [ ] Quand préférer Cypher (hiérarchies, patterns) vs pgRouting (Dijkstra routier)

---

{% include nav_phase.html prev_url="/missions/transition_1_2/" prev_label="Transition Phase 1→2" next_url="/missions/checkpoint_phase_2/" next_label="Checkpoint Phase 2" %}
