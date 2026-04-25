---
layout: default
title: NoSQL vs SQL
parent: Théorie
nav_order: 5
---

# NoSQL vs SQL : quand et pourquoi changer de paradigme

> Les bases relationnelles (SQL) règnent depuis 40 ans. Mais face aux données connectées, massives et peu structurées, de nouvelles approches émergent.

---

## Le modèle relationnel : forces et limites

**Forces** : maturité, ACID (Atomicité, Cohérence, Isolation, Durabilité), SQL standardisé, index B-tree.

**Limites rencontrées dans ce TD** :

| Problème | Exemple BDTOPO |
|----------|---------------|
| Hiérarchie profonde | `WITH RECURSIVE` sur 3 niveaux d'ontologie → verbeux, lent |
| Réseau de connexions | Trouver tous les chemins entre 2 POIs → N requêtes imbriquées |
| Schéma rigide | 22 tables BDTOPO avec des colonnes très différentes |
| Jointures multiples | Connecter POIs → routes → sommets → arêtes = 3+ JOIN |

> **Règle empirique** : au-delà de 5 jointures, le plan d'exécution SQL explose.

---

## Le théorème CAP

Dans un système distribué, on ne peut garantir que **2 sur 3** :

```
       Consistency (Cohérence)
          /\
         /  \
        /    \
   A  /      \  P
Availability    Partition tolerance
```

| Système | Choix CAP | Exemple |
|---------|-----------|---------|
| **PostgreSQL** | CA | Cohérent, disponible, pas de partition |
| **Neo4j** | CA | Cohérent, disponible, single-node par défaut |
| **Cassandra** | AP | Disponible, tolère les partitions, cohérence finale |
| **MongoDB** | CP | Cohérent (par défaut), tolère les partitions |

> **Notre cas** : BDTOPO en local (mono-nœud) → le CAP n'est pas le problème. C'est le **modèle de données** qui justifie le changement.

---

## Les 4 familles NoSQL

| Famille | Principe | Exemple | Cas d'usage |
|---------|----------|---------|-------------|
| **Clé-Valeur** | Dictionnaire géant | Redis, DynamoDB | Cache, sessions, compteurs |
| **Document** | JSON hiérarchique | MongoDB, CouchDB | Catalogues, CMS, API REST |
| **Colonne** | Lignes creuses massives | Cassandra, HBase | Time-series, logs, IoT |
| **Graphe** | Nœuds + Relations typées | **Neo4j**, JanusGraph | **Réseaux, ontologies, routage** |

**Pourquoi on utilise Neo4j dans ce cours** : BDTOPO a une ontologie hiérarchique (3 niveaux) et des POIs connectés par des distances. Le modèle graphe capture ces relations nativement.

---

## BASE : l'alternative à ACID

Les bases NoSQL adoptent souvent **BASE** au lieu d'ACID :

- **Basically Available** : le système répond toujours (même avec des données pas à jour)
- **Soft state** : l'état peut changer sans input (réplication)
- **Eventually consistent** : la cohérence arrive… avec le temps

> **Neo4j** est ACID (transactions) mais offre un modèle de données NoSQL (graphe). C'est un hybride.

---

## Quand choisir quoi ?

| Besoin | Outil | Pourquoi |
|--------|-------|----------|
| Agrégation statistique (COUNT, AVG, GROUP BY) | **SQL** | Moteur mature, optimiseur éprouvé |
| Filtrage spatial (ST_Intersects, ST_DWithin) | **PostGIS** | Pas d'équivalent natif dans Neo4j |
| Traversée de hiérarchie (parent → enfants → petits-enfants) | **Cypher** | `[:EST_SOUS_TYPE_DE*]` en 1 ligne |
| Plus court chemin dans un réseau | **pgRouting** | Dijkstra natif sur tables SQL |
| Tous les chemins entre A et B avec filtres | **Cypher** | Pattern matching déclaratif |
| Entreposage de milliards de lignes | **Colonne (Cassandra)** | Écriture massive |
| JSON semi-structuré variable | **Document (MongoDB)** | Pas de schéma fixe |

**Conclusion de ce cours** : on combine **PostGIS** (spatial) + **pgRouting** (routage) + **Neo4j** (ontologie + réseau). Aucun outil seul ne suffit.

---

## Pour aller plus loin

- [Slides théoriques]({% link _docs/theorie/bdd_nosql.md %}) — support visuel du cours magistral
- [Modèle BDTOPO]({% link _docs/theorie/bdtopo.md %}) — comprendre les données du TD
- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — le modèle graphe en détail
