# Opération Manticore — Plan de cours théorique (0.5J)

## Introduction (30 min)
- Présentation du fil conducteur : BDTOPO IGN & Analyse tactique.
- Pourquoi le SQL ne suffit plus ? (Complexité des réseaux, hiérarchies profondes).
- Objectifs du TD : PostGIS (Spatial) + pgRouting (Graphe routier) + Neo4j (Ontologie).

## Module 1 : Le mur du Relationnel (45 min)
- Rappels SQL & ACID.
- Le problème de la récursion : `WITH RECURSIVE` (syntaxe, performance, lisibilité).
- Jointures vs Traversées : Pourquoi 10 jointures tuent votre base de données.

## Module 2 : L'arsenal NoSQL (45 min)
- Théorème CAP & BASE (vs ACID).
- Panorama NoSQL : Clé-Valeur, Document, Colonne, Graphe.
- Focus Graphe : Modèle Labeled Property Graph (LPG) vs RDF.
- Pourquoi Neo4j ? Index-free adjacency.

## Module 3 : Intelligence Spatiale & Topologique (45 min)
- PostGIS : Géométries, Systèmes de projection (SRID), Index GIST.
- Topologie vs Géométrie : Pourquoi un simple `ST_Intersects` ne permet pas de calculer un itinéraire.
- pgRouting : Modèle de données (Source, Target, Cost) et algorithmes (Dijkstra, A*).

## Module 4 : Guerre Déclarative (30 min)
- SQL (Relationnel) vs Cypher (Pattern Matching).
- Comparaison des plans d'exécution.
- Introduction à l'IA pour la génération de requêtes (Mistral Vibe).

---
*Note : Ce cours prépare aux 4 FRAGOs du TD.*
