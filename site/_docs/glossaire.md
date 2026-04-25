---
layout: default
title: Glossaire
nav_order: 8
---

# Glossaire

> Les termes techniques utilisés dans ce cours.

---

## Bases de données

| Terme | Définition |
|-------|------------|
| **ACID** | Atomicité, Cohérence, Isolation, Durabilité — garanties des bases relationnelles |
| **BASE** | Basically Available, Soft state, Eventually consistent — alternative NoSQL |
| **CAP** | Théorème : Consistency, Availability, Partition tolerance — choisir 2/3 |
| **NoSQL** | Not Only SQL — bases non relationnelles (graphe, document, clé-valeur, colonne) |
| **LPG** | Labeled Property Graph — modèle de données de Neo4j (nœuds + relations typées + propriétés) |
| **Cypher** | Langage de requête déclaratif pour Neo4j, inspiré des patterns graphes |
| **Index-Free Adjacency** | Chaque nœud stocke les pointeurs vers ses voisins → O(1) par traversée |

## Spatial

| Terme | Définition |
|-------|------------|
| **PostGIS** | Extension spatiale de PostgreSQL (géométries, index GIST, fonctions ST_*) |
| **pgRouting** | Extension de routage pour PostgreSQL (Dijkstra, A*, etc.) |
| **SRID** | Spatial Reference Identifier — système de coordonnées. BDTOPO = **2154** (Lambert-93) |
| **EPSG:2154** | Lambert-93 — projection officielle pour la France métropolitaine |
| **EPSG:4326** | WGS84 — coordonnées GPS (latitude/longitude) |
| **ST_Intersects** | Teste si deux géométries se croisent |
| **ST_DWithin** | Teste si deux géométries sont dans un rayon donné |
| **ST_ClusterDBSCAN** | Algorithme de clustering spatial (density-based) |
| **ST_Transform** | Convertit entre systèmes de coordonnées |

## Données

| Terme | Définition |
|-------|------------|
| **BDTOPO** | Base de données topographique de l'IGN (objets du territoire français) |
| **EPCI** | Établissement Public de Coopération Intercommunale (communauté de communes, métropole, etc.) |
| **SIREN** | Identifiant unique d'un EPCI (9 chiffres) |
| **POI** | Point d'Interest — un objet géolocalisé pertinent (hôpital, aérodrome, caserne…) |
| **Ontologie** | Classification hiérarchique des objets BDTOPO (3 niveaux : Database → Object → Detail) |
| **CleABS** | Identifiant unique d'un objet dans la BDTOPO |

## Outils

| Terme | Définition |
|-------|------------|
| **Neo4j** | Base de données graphe (Java) utilisée dans ce cours pour l'ontologie et les traversées |
| **APOC** | Awesome Procedures On Cypher — plugin Neo4j avec 400+ algorithmes |
| **r2gg** | Route-Graph-Generator — convertit les tronçons BDTOPO en graphe navigable |
| **Gold Dumps** | Dumps SQL pré-calculés du graphe r2gg (tables `ways` + `ways_vertices_pgr`) |
| **Codestral** | Assistant IA de Mistral — utilisé pour générer des requêtes SQL/Cypher |
| **Marp** | Convertisseur Markdown → slides HTML/PDF |

## Concepts du TD

| Terme | Définition |
|-------|------------|
| **Choke point** | Nœud ou arête dont la suppression impacte le plus la connectivité du réseau |
| **Betweenness centrality** | Mesure de l'importance d'un nœud (combien de chemins passent par lui) |
| **Snap** | Associer un point à son nœud le plus proche dans le graphe |
| **Routage contraint** | Calcul d'itinéraire avec des règles (poids, largeur, vitesse) |
| **BBOX** | Bounding Box — rectangle englobant utilisé pour le filtrage spatial |
