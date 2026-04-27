---
layout: default
title: NoSQL vs SQL
parent: Théorie
nav_order: 5
---

# NoSQL vs SQL : pourquoi changer de paradigme ?

> **Comment Google, Netflix et Amazon ont dû inventer autre chose que les bases relationnelles — et ce que ça veut dire pour vous sur BDTOPO.**

---

## 1. Le problème : quand SQL atteint ses limites

PostgreSQL gère très bien les données sur **un seul serveur**. Mais regardons ce qu'on a dans ce TD :

- **30 Go** de données BDTOPO (toute la France)
- **22 tables** avec des colonnes très différentes (tronçons routiers, pylônes,-reservoirs, zones d'activité…)
- Des **relations hiérarchiques** sur 3 niveaux (Database → Object → Detail) via `parent_id`
- Un **réseau routier** de 20 millions de segments à relier bout-à-bout

Sur une seule machine, PostgreSQL fait le travail. Mais quand Google indexe le web entier, quand Netflix sert 200 millions d'abonnés, un seul serveur ne suffit plus. Il faut **distribuer les données sur 100 machines** — et c'est là que SQL montre ses limites.

---

## 2. ACID : ce que SQL garantit (et pourquoi c'est dur à distribuer)

ACID est l'acronyme de **Atomicité, Cohérence, Isolation, Durabilité** — les 4 garanties des transactions SQL.

**L'exemple du virement bancaire** : quand Alice envoie 100 € à Bob :

```
BEGIN;
  UPDATE comptes SET solde = solde - 100 WHERE id = 'Alice';
  UPDATE comptes SET solde = solde + 100 WHERE id = 'Bob';
COMMIT;
```

- **Atomicité** : c'est *tout ou rien* — jamais "Alice a perdu 100 € mais Bob n'a rien reçu".
- **Cohérence** : la somme des comptes ne change pas.
- **Isolation** : pendant la transaction, les autres ne voient rien de bizarre.
- **Durabilité** : une fois le COMMIT fait, même si le serveur crash, c'est enregistré.

**Le problème distribué** : sur 1 serveur, ACID est facile — une seule machine gère tout. Sur **100 serveurs répartis sur 3 continents**, une transaction implique de coordonner les 100 machines. Chaque aller-retour réseau coûte des millisecondes ; avec 100 serveurs, une transaction prend des secondes au lieu de millisecondes. NoSQL choisit souvent de **relâcher ACID** pour gagner en vitesse et en scalabilité.

> **NoSQL ne veut pas dire "pas d'ACID"** — ça veut dire "Not Only SQL". CouchDB, MongoDB en mode cluster, et même Neo4j en local respectent ACID. C'est le *modèle de données* (graphe, document…) qui change, pas la fiabilité.

---

## 3. Le théorème CAP

Dans un système distribué, on ne peut garantir que **2 sur 3** :

```
              Consistency
                 /\
                /  \
               /    \
          A  /        \  P
     Availability  Partition
        tolerance
```

- **C** (Consistency) : tous les nœuds voient les mêmes données au même moment
- **A** (Availability) : le système répond toujours, même si certains nœuds sont down
- **P** (Partition tolerance) : le système continue de fonctionner même si le réseau coupe en deux

| Système | Choix | Pourquoi |
|---------|-------|---------|
| **PostgreSQL** (mono-nœud) | CA | Pas de partition réseau à gérer — cohérence totale |
| **Neo4j** (single-node) | CA | Même raisonnement — cohérence locale |
| **Cassandra** | AP | Priorité : disponibilité → les données sont "éventuellement" cohérentes |
| **MongoDB** (par défaut) | CP | Priorité : cohérence stricte → peut refuser des lectures si partition |

> **Notre cas** : BDTOPO en local (mono-nœud) → le CAP n'est pas le problème. C'est le **modèle de données** qui justifie le passage à Neo4j pour l'ontologie et à pgRouting pour le routage.

---

## 4. Les 4 familles NoSQL

```
+------------+  +----------------+  +-----------------+  +----------+
| Clé-Valeur |  |    Document    |  |    Colonne      |  |  Graphe  |
+------------+  +----------------+  +-----------------+  +----------+
|   Redis    |  |   MongoDB      |  |   Cassandra    |  |  Neo4j   |
+------------+  +----------------+  +-----------------+  +----------+
```

| Famille | Analogie | Cas d'usage | Limite |
|---------|----------|-------------|--------|
| **Clé-Valeur** | Vestiaire : le jeton → votre manteau | Cache, sessions, jetons API | Impossible de chercher "donne-moi tous les manteaux rouges" |
| **Document** | Dossier patient : chaque patient a des champs différents | CMS, catalogues produits, profils utilisateurs | Transactions multi-documents limitées |
| **Colonne** | Tableur où chaque ligne peut avoir des colonnes différentes | Analytics massifs, IoT, time-series | Modèle complexe à concevoir |
| **Graphe** | Plan de métro : gares = nœuds, lignes = relations | Réseaux sociaux, routage, ontologies | Pas adapté aux agrégats massifs (OLAP) |

**Pourquoi Neo4j dans ce cours** : BDTOPO a une ontologie à 3 niveaux liée par `parent_id` et des POIs connectés par des distances. Le modèle graphe stocke ces relations comme des **pointeurs directs** entre nœuds —找到 les amis de Jean = suivre les pointeurs, pas parcourir un index.

---

## 5. BASE : le pendant de ACID

Si ACID = rigueur (virement bancaire : tout ou rien), BASE = **pragmatique** :

> **Basically Available** : le système répond toujours, même si les données ne sont pas tout-à-fait à jour.
> **Soft state** : l'état peut changer sans requête — à cause de la réplication en arrière-plan.
> **Eventually consistent** : la cohérence arrive… avec un petit délai.

**Exemple concret** : le fil d'actualités Twitter. Deux amis voient votre tweet dans un ordre légèrement différent pendant 1 seconde → **acceptable**. Votre banque débite votre compte mais n'enregistre pas le virement → **inacceptable**. BASE, c'est OK pour les données "au mieux à jour" ; ACID, c'est obligatoire pour les données financières.

**Neo4j est hybride** : transactions ACID en local, mais le modèle de données est un graphe (NoSQL). PostgreSQL + PostGIS + pgRouting + Neo4j — chaque outil pour ce qu'il fait de mieux.

---

## 6. Guide de choix : SQL ou NoSQL ?

| Besoin | Outil recommandé | Pourquoi |
|--------|-----------------|----------|
| Agrégation statistique (COUNT, AVG, GROUP BY) | **SQL** | Moteur mature, optimiseur prouvé |
| Filtrage spatial (ST_Intersects, ST_DWithin) | **PostGIS** | Pas d'équivalent natif dans Neo4j |
| Ontologie hiérarchique (parent → enfants → petits-enfants) | **Cypher** | `[:EST_SOUS_TYPE_DE*]` en 1 requête |
| Plus court chemin dans un réseau routier | **pgRouting** | Dijkstra natif sur tables SQL |
| Tous les chemins entre A et B avec filtres | **Cypher** | Pattern matching déclaratif, très lisible |
| Milliards de lignes à écrire rapidement | **Colonne (Cassandra)** | Écriture massive append-only |
| JSON semi-structuré (champs variables par document) | **Document (MongoDB)** | Schéma flexible, pas de migration |
| Données connectées : sociaux, réseaux, itinéraires | **Graphe (Neo4j)** | Index-Free Adjacency — chaque saut est O(1) |

**Conclusion du cours Manticore** :

- **PostGIS** → données spatiales brutes, filtrage par zone
- **pgRouting** → calcul d'itinéraires sur le graphe routier
- **Neo4j** → ontologie hiérarchique + relations POIs, exploration du réseau

Aucun outil seul ne suffit. La puissance vient de leur **combinaison**.

---

## Pour aller plus loin

- [BDTOPO et le modèle relationnel]({% link _docs/theorie/bdtopo.md %}) — comprendre les données du TD
- [BDD NoSQL : support visuel]({% link _docs/theorie/bdd_nosql.md %}) — slides du cours magistral
- [GraphDB 101]({% link _docs/theorie/graphdb_101.md %}) — Index-Free Adjacency et Cypher en détail
- [pgRouting et r2gg]({% link _docs/theorie/pgrouting_et_r2gg.md %}) — routage sur PostGIS
