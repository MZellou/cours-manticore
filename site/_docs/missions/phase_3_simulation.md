---
title: Phase 3 — Simulation
parent: Missions
nav_order: 4
layout: default
---
# Phase 3 — Simulation d'attaque

> *"Simuler une attaque sur le réseau et comparer les approches SQL vs Graphe."*

**Mode** : Groupe (les 4 rôles collaborent sur la simulation).
**Durée estimée** : 5h (benchmark 1h30 + simulation itérative 2h + analyse réseau 1h + rédaction 30min)

---

## Comprendre : quand Cypher est-il réellement supérieur à SQL ?

Avant de simuler, il faut comprendre **pourquoi** on utilise deux moteurs.
La réponse n'est pas "Cypher est toujours mieux" — c'est **chaque outil excelle sur des formes de requêtes différentes**.

### Rappel du modèle de données

```
Neo4j :                        PostGIS :
┌─────────────────────┐        ┌──────────────────────────┐
│ (:ClasseOntologie)  │        │ bdtopo_ontology          │
│   .name             │        │   id, name, obj_type,    │
│   .obj_type         │        │   parent_id              │
│                     │        ├──────────────────────────┤
│ -[:EST_SOUS_TYPE_DE]│        │ mission_pois             │
│                     │        │   role, source, nature,   │
│ (:POI)              │        │   nom, geom              │
│   .role, .source    │        ├──────────────────────────┤
│   .nature, .nom     │        │ ways / ways_vertices_pgr │
│                     │        │   source, target, cost   │
│ -[:DISTANCE {meters}]│       └──────────────────────────┘
└─────────────────────┘
```

---

## Partie A — Benchmark structuré (1h30)

### T1 — Choke Points : deux approches, deux mondes

Un choke point est un nœud ou une arête dont la suppression **maximise l'impact**
sur la connectivité du réseau.

**Approche SQL** : trouvez un chemin de référence avec `pgr_dijkstra`, puis pour chaque arête, bloquez-la (`cost = -1`) et recalculez.
*Limitation : nécessite une boucle Python.*

**Approche Neo4j** : calcul de **betweenness centrality** en une seule requête APOC.

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t1--choke-points)

### T2 — Requêtes croisées : là où Cypher brille

Essayez ces requêtes dans Neo4j Browser et réfléchissez à l'équivalent SQL.

#### 2a — Tous les chemins entre deux rôles

Trouvez tous les chemins entre un POI attaque et un POI défense (Hôpital), avec les étapes et la distance.
*Indice : `MATCH path = ...-[:DISTANCE*]-(...) RETURN reduce(...)`*

#### 2b — Plus court chemin avec nœud intermédiaire obligatoire

Trouvez le chemin attaque → ravitaillement → énergie le plus court.
*Indice : deux `shortestPath` enchaînés.*

#### 2c — Sous-graphe accessible depuis un POI

Trouvez tous les POIs accessibles en 2 sauts depuis un aérodrome.
*Indice : `apoc.path.subgraphAll` avec `maxLevel: 2`.*

→ [Corrigé T2a-T2c]({% link _docs/corriges/corrige_phase_3.md %}#t2a--tous-les-chemins-entre-deux-roles)

### T3 — Tableau benchmark

Reproduisez ce tableau avec vos mesures (`EXPLAIN ANALYZE` pour SQL, `PROFILE` pour Cypher) :

| # | Requête | SQL (ms) | Cypher (ms) | LOC SQL | LOC Cypher | Gagnant |
|---|---------|----------|-------------|---------|------------|---------|
| 1 | Sous-types de "Tronçon de route" | | | | | |
| 2 | Tous les chemins attaque → défense | | | | | |
| 3 | Betweenness centrality (choke points) | | | | | |
| 4 | POIs à < 500m d'une route (`ST_DWithin`) | | | | | |
| 5 | Plus court chemin avec nœud intermédiaire | | | | | |

**Requête 1** : traversée ontologique ("Tronçon de route" → tous les sous-types)
**Requête 4** : spatiale — POIs à moins de 500m d'une route (ici SQL gagne)

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t3--requetes-benchmark)

### T4 — Synthèse : quand utiliser quoi

Complétez ce tableau dans votre rapport :

| Situation | Outil | Pourquoi |
|-----------|-------|----------|
| Filtrer des POIs par attributs (nature, catégorie) | | |
| Calculer un buffer spatial (ST_Buffer) | | |
| Trouver le plus court chemin routier | | |
| Parcourir une hiérarchie de types | | |
| Centralité / betweenness d'un nœud | | |
| Joindre des données géographiques | | |
| Requête pattern matching (chemin multi-étapes) | | |
| Agrégation statistique (COUNT, AVG, GROUP BY) | | |

---

## Partie B — Simulation itérative (2h)

> On passe de la théorie à la pratique : coupez des arêtes et mesurez les conséquences.

### T5 — Couper 1 arête, mesurer l'impact

Choisissez une arête identifiée comme **choke point** (cf. T1) et bloquez-la.

**Objectifs** :
1. Sauvegarder les coûts originaux (`CREATE TABLE ways_backup AS SELECT * FROM ways`)
2. Bloquer l'arête (`UPDATE ways SET cost = -1, reverse_cost = -1 WHERE id = ...`)
3. Mesurer la distance entre 2 POIs avant/après (détour en %)
4. Comparer le temps de calcul SQL vs Cypher

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t5--couper-1-arte)

### T6 — Couper 3 arêtes, dégradation cumulative

Bloquez 3 arêtes **stratégiquement** et mesurez la dégradation cumulative.

Documentez dans un tableau :

| Arête coupée | Distance A→B | POIs isolés | Composantes connexes |
|-------------|-------------|-------------|---------------------|
| Aucune (réf.) | | | |
| Edge 1 seul | | | |
| Edge 1 + 2 | | | |
| Edge 1 + 2 + 3 | | | |

> **Question clé** : la dégradation est-elle linéaire ou exponentielle ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t6--couper-3-artes)

### T7 — Stratégie défensive (protéger 5 arêtes)

Vous êtes le **rôle Défense**. Choisissez 5 arêtes à **protéger**.

**Critère** : maximiser le nombre de POIs défense qui restent accessibles après l'attaque.

**Méthode** :
1. L'agent Attaque identifie ses 5 arêtes cibles
2. L'agent Défense identifie ses 5 arêtes à protéger
3. Si une arête est ciblée ET protégée → elle tient
4. Mesurez l'état final du réseau

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t7--stratgie-dfensive)

### T8 — Stratégie offensive (couper 5 arêtes)

Vous êtes le **rôle Attaque**. Trouvez les 5 arêtes dont la coupure **maximise les dégâts**.

*Indice : pour chaque arête "importante", simuler la coupure et calculer `distance_moyenne_après - distance_moyenne_avant`. Les 5 plus gros impacts = vos cibles.*

**Mesurez** :
- Nombre de POIs devenus inatteignables
- Augmentation moyenne de distance entre POIs
- Nombre de composantes connexes créées

> **Défi** : comparez votre stratégie avec un autre groupe. Qui a causé le plus de dégâts ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t8--stratgie-offensive)

---

## Partie C — Analyse de réseau (1h)

### T9 — Composantes connexes avant/après destruction

**Objectif** : utiliser `pgr_connectedComponents` et vérifier la connexité du graphe POI.

**Analysez** :
1. Combien de composantes avant destruction ?
2. Et après avoir coupé 3 arêtes ? 5 arêtes ?
3. Y a-t-il des POIs "îles" (composante de taille 1) ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t9--composantes-connexes)

### T10 — Centralité de degré : les hubs du réseau

**Objectif** : calculer le degré de chaque POI (nombre de voisins) et identifier les hubs.

**Interprétation** :
- Degré élevé = **hub** (bien connecté)
- Couper un hub → impact maximal
- Protéger un hub → priorité défensive

**Exercice** : les hubs identifiés correspondent-ils aux choke points de la T1 ? Pourquoi ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_3.md %}#t10--centralit-de-degr)

### T11 — Carte de situation finale

```bash
python scripts/04_benchmark_comparison.py --role <votre_role> --map data/carte_situation.png
```

La carte doit montrer :
- POIs des 4 rôles (couleurs distinctes)
- Choke points identifiés
- Routes normales vs contraintes
- Impact de la destruction (routes coupées, POIs isolés)

---

## Partie D — Rédaction du rapport (30min)

### T12 — Synthèse finale

Complétez le rapport de groupe avec :

1. **Résumé exécutif** : 5 phrases max sur la résilience de votre EPCI
2. **Chiffres clés** : nombre de POIs, clusters, choke points, % réseau dégradé
3. **Benchmark** : le tableau T3 complété avec vos mesures
4. **Leçon apprise** : SQL vs Cypher — dans quel cas chaque outil a gagné ?
5. **Recommandations** : si vous deviez renforcer le réseau, par où commencer ?

---

## Indices Codestral

```
"Montre un exemple concret où Cypher (Neo4j) est nettement supérieur à SQL :
trouver tous les chemins entre un aérodrome et un hôpital en passant par
au moins un réservoir, avec la distance totale. Écris le SQL équivalent
pour comparer la complexité."
```

```
"Comment simuler la destruction d'une arête dans un graphe pgRouting et
mesurer l'impact sur la connectivité ? Écris une boucle Python qui
teste chaque arête d'un chemin et calcule le détour moyen."
```

```
"Écris une requête Cypher qui calcule la centralité de degré de chaque
POI dans un réseau, puis identifie les hubs (degré > 2× la moyenne)."
```

---

## Critères de validation

- [ ] Betweenness centrality exécutée sur Neo4j (top 5 POIs identifiés)
- [ ] Requêtes 2a-2c fonctionnelles dans Neo4j Browser
- [ ] Tableau benchmark complété (5 requêtes, temps mesurés, LOC comptées)
- [ ] Requête 4 montre que SQL gagne sur le spatial
- [ ] Tableau synthèse T4 complété
- [ ] T5-T6 : au moins 3 arêtes coupées, dégradation mesurée et documentée
- [ ] T7 : stratégie défensive formulée (5 arêtes protégées + justification)
- [ ] T8 : stratégie offensive formulée (5 arêtes ciblées + impact mesuré)
- [ ] T9 : composantes connexes avant/après comparées
- [ ] T10 : hubs identifiés, corrélation avec choke points analysée
- [ ] T11 : carte PNG générée
- [ ] T12 : rapport synthèse complété
