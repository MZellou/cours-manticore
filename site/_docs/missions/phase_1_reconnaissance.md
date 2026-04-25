---
title: Phase 1 — Reconnaissance
parent: Missions
nav_order: 2
layout: default
---
# Phase 1 — Reconnaissance

> *"Identifier les POIs critiques de votre EPCI selon votre assignation."*

**Mode** : Solo (chaque agent travaille sur son rôle).
**Durée estimée** : 4h (warm-up 1h + tâches 1h30 + exploration 1h30)

---

## Prérequis

- Docker stack lancé (PostGIS + Neo4j)
- Données chargées : `python scripts/00_setup.py --epci "<votre EPCI>"`
- Votre briefing rôle dans `mission/roles/<votre_role>.md`

---

## Warm-up — Réactivation SQL & Découverte Cypher (1h)

> Avant d'attaquer les POIs, remettons les bases en main.

### T0a — SQL : GROUP BY, HAVING, ORDER BY

La table `zone_d_activite_ou_d_interet` contient ~596k lignes. Explorez-la :

**Objectifs** :
1. Lister les catégories et leur nombre (`GROUP BY`)
2. Filtrer les catégories avec > 10 000 entrées (`HAVING`)
3. Explorer les natures dans la catégorie 'Santé'

**Exercice** : trouvez combien il y a de gendarmeries ET de casernes dans votre EPCI.
*Indice : filtrez sur `categorie` ET `nature`.*

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t0a--sql--group-by-having-order-by)

### T0b — SQL : Jointures spatiales

Croisez deux tables avec une jointure spatiale (`ST_Intersects`, `ST_DWithin`).

**Objectif** : quels équipements de transport sont dans une zone industrielle ?

**Exercice** : combien d'aérodromes sont à moins de 2 km d'un hôpital ?
*Indice : `ST_DWithin` avec un rayon de 2000m entre `aerodrome` et `zone_d_activite_ou_d_interet`.*

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t0b--sql--jointures-spatiales)

### T0c — Cypher : premiers pas dans Neo4j

Ouvrez [http://localhost:7474](http://localhost:7474). L'ontologie est déjà chargée.

**Objectifs** :
1. Lister les nœuds de l'ontologie (`MATCH`)
2. Trouver les enfants de "Tronçon de route"
3. Compter les nœuds par label

**Exercice** : trouvez tous les "Detail" qui sont des sous-types de "Construction ponctuelle". Combien y en a-t-il ?

> **Note** : si les POIs ne sont pas encore dans Neo4j, vous les migrerez dans la Phase 2.

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t0c--cypher--premiers-pas)

---

## Tâches principales (1h30)

### T1 — Explorer l'ontologie BDTOPO

L'ontologie a 3 niveaux hiérarchiques : Database → Object → Detail.

**Objectif** : traverser la hiérarchie depuis "Tronçon de route" vers ses sous-types.
*Indice : `WITH RECURSIVE` + `parent_id`.*

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t1--explorer-lontologie-bdtopo)

### T2 — Sélectionner les POIs de votre rôle

Consultez votre briefing rôle (`mission/roles/<votre_role>.md`) pour connaître :
- Les tables BDTOPO à interroger
- Les filtres (nature, catégorie, importance)
- Les jointures spatiales à effectuer

**Objectif** : écrire vos requêtes et insérer les résultats dans `mission_pois`.
*Indice : `INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom) SELECT ...`*

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t2--slectionner-les-pois-de-votre-rle)

### T3 — Ajouter des critères de criticité

Enrichissez vos POIs avec des critères d'importance :
- Postes électriques : `CAST(importance AS INTEGER) <= 3`
- Aérodromes : `categorie IN ('Internationale', 'Nationale')`
- Zones militaires : `categorie = 'Administratif ou militaire'`

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t3--ajouter-des-critres-de-criticite)

### T4 — Clusteriser les POIs (ST_ClusterDBSCAN)

Détectez les grappes tactiques de POIs proches.

**Objectif** : utiliser `ST_ClusterDBSCAN` avec `eps := 2000` et `minpoints := 2`.
Interprétez : où sont les zones de concentration stratégique ?

**Exercice bonus** : variez `eps` (1000, 3000, 5000). Comment évolue le nombre de clusters ?

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t4--clusteriser-les-pois-st_clusterdbscan)

### T5 — Partager vos POIs avec votre groupe

En fin de phase 1, les 4 agents fusionnent leurs POIs dans `mission_pois` (table partagée).

**Vérifiez** : chaque rôle doit apparaître avec au moins 1 source.
*Indice : `SELECT role, source, count(*) FROM mission_pois GROUP BY role, source`*

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t5--partager-vos-pois)

---

## Exploration libre guidée (1h30)

### T6 — Questions bonus par rôle

Chaque rôle a des **questions bonus** dans son briefing. Résolvez-en au moins 2.
Voir votre page rôle : [Attaque]({% link _docs/roles/attaque.md %}), [Défense]({% link _docs/roles/defense.md %}), [Ravitaillement]({% link _docs/roles/ravitaillement.md %}), [Énergie]({% link _docs/roles/energie.md %}).

**Principe** : ces questions vous font croiser les tables et utiliser des fonctions SQL que vous n'avez pas encore pratiquées (`ST_Buffer`, `ST_Union`, window functions, sous-requêtes corrélées).

→ [Corrigé Rôles bonus]({% link _docs/corriges/corrige_roles_bonus.md %})

### T7 — Cross-rôle : échangez avec vos coéquipiers

Chaque agent prépare **une question** pour un autre rôle et la lui transmet.

| Demandeur | Question à poser à… | Exemple |
|-----------|---------------------|---------|
| **Défense** → Énergie | "Quels postes HT sont à moins de 1 km d'un hôpital ?" | Croisement santé + énergie |
| **Attaque** → Ravitaillement | "Quels ports sont les plus proches d'une caserne ?" | Cibles logistiques |
| **Énergie** → Défense | "Combien de ponts croisent une ligne THT ?" | Points fragiles |
| **Ravitaillement** → Attaque | "Y a-t-il des zones industrielles à moins de 3 km d'un aérodrome ?" | Couverture aérienne |

L'agent interrogé doit écrire et exécuter la requête SQL. Documentez la requête et le résultat dans le rapport.

→ [Corrigé]({% link _docs/corriges/corrige_phase_1.md %}#t7--cross-rle)

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

```
"Écris une requête SQL qui utilise ST_DWithin pour trouver tous les
équipements de transport à moins de N mètres d'une zone d'activité.
Inclus un GROUP BY pour compter par type."
```

---

## Critères de validation

- [ ] Warm-up : les 3 exercices T0a-T0c complétés
- [ ] `SELECT count(*) FROM mission_pois WHERE role = 'votre_role'` → > 0
- [ ] Chaque source de POI identifiée dans le briefing retourne des résultats
- [ ] ST_ClusterDBSCAN détecte au moins 1 cluster
- [ ] Au moins 2 questions bonus (T6) résolues
- [ ] Au moins 1 cross-rôle (T7) documenté
- [ ] Requêtes documentées dans le rapport (avec commentaires)
