---
layout: default
title: Contenu des données BDTOPO
parent: Théorie
nav_order: 2
---

> Généré automatiquement. Fichiers source : `data/poi_source/*.parquet` + `data/epci.parquet`.

---

## 1. Tables disponibles (22 fichiers, ~30 Go total)

| Table | Rows | Type géom | Colonnes clés | Intérêt pédagogique |
|---|---|---|---|---|
| **aerodrome** | 1 382 | Point | `categorie`, `nature`, `code_icao`, `altitude` | Attaque : aérodromes internationaux/nationaux |
| **piste_d_aerodrome** | 2 014 | Surf. | `nature`, `fonction` | Complément aérodromes |
| **pylone** | 265 143 | Point | `hauteur` | Énergie : réseau électrique (265k pylônes !) |
| **poste_de_transformation** | 4 104 | Point | `importance` (1-6) | Énergie : postes critiques (importance ≤ 3) |
| **ligne_electrique** | 14 470 | Line | `voltage` | Énergie : lignes THT (400kV, 225kV) |
| **zone_d_activite_ou_d_interet** | 595 892 | Surf. | `categorie`, `nature`, `nature_detaillee`, `toponyme`, `importance` | **Table maître** : tous POIs administratifs, militaires, santé, industrie, sport… |
| **equipement_de_transport** | 182 235 | Point/Surf. | `nature`, `nature_detaillee`, `toponyme` | Ports, gares, parkings, aérogares, échangeurs |
| **construction_ponctuelle** | 319 133 | Point | `nature`, `nature_detaillee`, `hauteur` | Antennes, éoliennes, transformateurs, cheminées, puits |
| **construction_surfacique** | 20 476 | Surf. | `nature`, `nature_detaillee` | Ponts, barrages, écluses |
| **construction_lineaire** | 939 141 | Line | `nature`, `nature_detaillee` | Ponts linéaires, barrages, murs, tunnels, quais |
| **reservoir** | 91 737 | Surf. | `nature`, `volume`, `hauteur` | Ravitaillement/Énergie : réservoirs industriels, châteaux d'eau |
| **terrain_de_sport** | 139 272 | Surf. | `nature`, `nature_detaillee` | Peu pertinent militairement |
| **canalisation** | 7 906 | Line | `nature` | Énergie : hydrocarbures (1 169), autres (6 737) |
| **foret_publique** | 17 249 | Surf. | `nature` | Défense : couverture forestière |
| **parc_ou_reserve** | 6 942 | Surf. | `nature`, `nature_detaillee` | Contexte : zones protégées, Natura 2000 |
| **troncon_de_voie_ferree** | 104 717 | Line | `nature`, `usage`, `electrifie`, `nombre_de_voies`, `vitesse_maximale` | Ravitaillement : voies fret, LGV |
| **troncon_de_route** | 20 128 325 | Line | `nature`, `importance`, `largeur_de_chaussee`, `restriction_de_poids_total`, `restriction_de_hauteur`, `sens_de_circulation`, `vitesse_moyenne_vl`, `urbain` | **Réseau routier** : graphe pour pgRouting/r2gg |
| cours_d_eau | 487 700 | Line | — | Non POI |
| surface_hydrographique | 666 000 | Surf. | — | Non POI |
| places_france | ~2M | Point | — | À explorer (geoparquet) |

---

## 2. Nomenclature BDTOPO — Valeurs clés par table

### 2.1 aerodrome (1 382 rows)

| categorie | nature | count |
|---|---|---|
| Autre | Héliport | 705 |
| Nationale | Aérodrome | 341 |
| Autre | Aérodrome | 154 |
| Internationale | Aérodrome | 96 |
| Autre | Altiport | 73 |
| Nationale | Héliport | 6 |
| Autre | Hydrobase | 3 |

### 2.2 zone_d_activite_ou_d_interet (595 892 rows) — Top 40

| categorie | nature | nature_detaillee | count |
|---|---|---|---|
| Culture et loisirs | Espace public | Place | 36 907 |
| Administratif ou militaire | Mairie | — | 34 792 |
| Religieux | Culte chrétien | Eglise | 33 717 |
| Gestion des eaux | Station de pompage | — | 19 513 |
| Science et enseignement | Enseignement primaire | Ecole élémentaire | 18 086 |
| Culture et loisirs | Monument | Monument aux morts | 17 628 |
| Science et enseignement | Enseignement primaire | Ecole primaire | 16 606 |
| Gestion des eaux | Station d'épuration | — | 14 588 |
| Culture et loisirs | Aire de détente | — | 13 482 |
| Science et enseignement | Enseignement primaire | Ecole maternelle | 13 482 |
| Religieux | Culte chrétien | Chapelle | 12 436 |
| **Sport** | **Autre équipement sportif** | Terrain de sport | 10 283 |
| Culture et loisirs | Espace public | Square | 9 962 |
| Culture et loisirs | Salle de spectacle ou conférence | Salle polyvalente | 9 922 |
| Sport | Complexe sportif couvert | Gymnase | 9 232 |
| Culture et loisirs | Camping | — | 8 057 |
| **Santé** | **Maison de retraite** | — | 7 842 |
| Science et enseignement | Collège | — | 7 501 |
| **Administratif ou militaire** | **Poste** | Bureau de poste | 7 409 |
| Science et enseignement | Enseignement supérieur | — | 3 218 |
| **Administratif ou militaire** | **Gendarmerie** | — | 3 163 |
| **Industriel et commercial** | **Zone industrielle** | — | 6 363 |
| **Industriel et commercial** | **Zone industrielle** | Zone d'activités | 5 245 |
| **Industriel et commercial** | **Déchèterie** | — | 5 024 |
| **Industriel et commercial** | **Divers industriel** | Poste de gaz | 4 808 |
| **Industriel et commercial** | **Usine** | — | 3 286 |
| Culture et loisirs | Point de vue | — | 4 044 |
| **Santé** | **Hôpital** | — | (dans top 50) |
| **Administratif ou militaire** | **Caserne** | — | (dans top 80) |

**Catégories utiles par rôle :**

| Rôle | filtre categorie | filtre nature |
|---|---|---|
| Attaque | Administratif ou militaire | Gendarmerie, Caserne, Camp militaire |
| Défense | Santé / Administratif ou militaire | Hôpital, Maison de retraite, Gendarmerie |
| Ravitaillement | Industriel et commercial | Zone industrielle, Usine, Marché |
| Énergie | (via tables dédiées) | — |
| Industries | Industriel et commercial | Zone industrielle, Usine, Déchèterie, Divers industriel |

### 2.3 equipement_de_transport (182 235 rows)

| nature | nature_detaillee | count |
|---|---|---|
| Service dédié aux véhicules | Borne de rechargement électrique | 67 071 |
| Parking | — | 64 996 |
| Parking | Parking touristique isolé | 10 746 |
| **Carrefour** | **Rond-point** | 9 142 |
| Carrefour | — | 9 103 |
| **Carrefour** | **Échangeur complet** | 1 678 |
| **Station de tramway** | — | 1 627 |
| **Port** | **Port de plaisance** | 976 |
| **Port** | **Port de commerce** | 114 |
| **Port** | **Port de pêche** | 94 |
| **Port** | **Bassin** | 114 |
| **Port** | — | 485 |
| **Gare voyageurs et fret** | — | 685 |
| **Gare voyageurs uniquement** | — | 584 |
| **Gare fret uniquement** | — | 369 |
| **Aérogare** | — | 172 |
| Tour de contrôle aérien | — | 152 |
| Gare routière | — | 426 |
| Aire de repos ou de service | Aire de repos | 915 |

### 2.4 construction_ponctuelle (319 133 rows)

| nature | nature_detaillee | count |
|---|---|---|
| Antenne | Antenne-relais | 42 589 |
| **Transformateur** | — | 28 841 |
| **Éolienne** | — | 10 351 |
| Autre construction élevée | — | 6 020 |
| **Cheminée** | — | 5 489 |
| **Puits d'hydrocarbures** | Puits de pétrole | 528 |
| **Torchère** | — | 329 |
| **Phare** | — | 247 |
| Antenne | Tour hertzienne | 274 |
| Autre construction élevée | Tour de guet | 284 |
| Puits d'hydrocarbures | Puits de gaz | 211 |

### 2.5 construction_surfacique (20 476 rows)

| nature | count |
|---|---|
| Pont | 16 175 |
| **Barrage** | 400 |
| Écluse | 2 620 |
| Pont | Pont-canal (247), Viaduc (145) |

### 2.6 reservoir (91 737 rows)

| nature | count |
|---|---|
| Réservoir d'eau ou château d'eau au sol | 46 243 |
| **Réservoir industriel** | 32 349 |
| Château d'eau | 11 545 |

### 2.7 ligne_electrique (14 470 rows)

| voltage | count |
|---|---|
| 63 kV | 6 672 |
| **225 kV** | 3 351 |
| 90 kV | 2 784 |
| **400 kV** | 1 364 |
| 150 kV | 113 |

### 2.8 troncon_de_route (20 128 325 rows) — Champs de routage

| nature | count |
|---|---|
| Route à 1 chaussée | 10 581 438 |
| Chemin | 3 951 578 |
| Route empierrée | 2 493 834 |
| Sentier | 2 349 974 |
| Rond-point | 376 971 |
| Route à 2 chaussées | 211 967 |
| Type autoroutier | 73 783 |
| Bretelle | 44 526 |

| importance | count |
|---|---|
| 1 (national) | 68 995 |
| 2 | 543 789 |
| 3 | 1 086 588 |
| 4 | 2 018 854 |
| 5 (local) | 13 835 878 |
| 6 | 2 574 221 |

**Contraintes de routage disponibles :**
- `restriction_de_poids_total` : 3.5t à 19t (ex: 18 797 tronçons à 3.5t)
- `restriction_de_hauteur` : présent sur ~5% du réseau
- `restriction_de_largeur` : rare
- `largeur_de_chaussee` : 0 à 10+ m (dominante 3-5m)
- `vitesse_moyenne_vl` : 0, 1, 10, 20, 25 km/h…
- `sens_de_circulation` : Double sens / Sens direct / Sens inverse
- `urbain` : True/False

---

## 3. EPCIs sélectionnés (30)

### 3.1 Critères de sélection

Les EPCIs sont choisis pour maximiser la **diversité géographique et thématique** :
- Grandes métropoles (Paris, Lyon, Marseille…)
- Zones frontalières (Strasbourg, Lille, Dunkerque, Cattenom)
- Littoral (Brest, Le Havre, Cotentin, Île de Ré, Ajaccio, Saint-Malo)
- Montagne (Grenoble, Pays Basque)
- Zones à centrales nucléaires proches (Cattenom, Cotentin/Flamanville, Ardenne/Chooz, Dunkerque/Gravelines, Grand Poitiers/Civaux)
- Zones militaires historiques (Verdun, Châlons-en-Champagne, Reims)
- Taille variée : de CC de l'Île de Ré (~13k routes) à Métropole du Grand Paris (~356k routes)

### 3.2 Centrales nucléaires proches

Les centrales ne sont PAS dans BDTOPO. Coordonnées approximatives utilisées :

| Centrale | Coords | EPCI le plus proche |
|---|---|---|
| Gravelines | (2.14, 51.0) | CU de Dunkerque |
| Flamanville | (-1.85, 49.55) | CA du Cotentin |
| Chooz | (4.82, 50.08) | Ardenne Métropole |
| Cattenom | (6.25, 49.42) | CC de Cattenom et Environs |
| Civaux | (0.65, 46.45) | CU du Grand Poitiers |
| Penly | (1.22, 49.97) | (CC Falaises du Talou — pas sélectionné) |
| Tricastin | (4.75, 44.35) | (CC Drôme Sud Provence — pas sélectionné) |
| Cruas | (4.65, 44.60) | CA Montélimar Agglomération |

### 3.3 Matrice POI par EPCI

| EPCI | aérod. | zone_act. | equip_transp | constr_ponct. | constr_surf. | réservoir | ligne_élec. | poste_transf. | voie_ferrée |
|---|---|---|---|---|---|---|---|---|---|
| **Métropole du Grand Paris** | 18 | 24 040 | 14 366 | 2 481 | 1 387 | 1 255 | 222 | 123 | 7 521 |
| **Métropole d'Aix-Marseille-Provence** | 22 | 9 383 | 4 488 | 3 478 | 450 | 2 706 | 390 | 95 | 3 174 |
| **Métropole de Lyon** | 11 | 7 304 | 2 572 | 1 535 | 271 | 960 | 232 | 46 | 2 987 |
| **Métropole Européenne de Lille** | 6 | 5 208 | 2 405 | 1 350 | 185 | 498 | 112 | 30 | 789 |
| **Toulouse Métropole** | 8 | 3 280 | 2 983 | 947 | 229 | 275 | 92 | 27 | 512 |
| **Eurométropole de Strasbourg** | 7 | 3 284 | 1 408 | 738 | 282 | 438 | 99 | 19 | 1 568 |
| **Métropole Rouen Normandie** | 7 | 3 554 | 1 662 | 882 | 132 | 816 | 130 | 30 | 1 330 |
| **Grenoble-Alpes-Métropole** | 11 | 2 706 | 1 204 | 781 | 110 | 526 | 147 | 25 | 515 |
| **CU du Grand Reims** | 9 | 3 578 | 769 | 1 208 | 117 | 679 | 91 | 24 | 674 |
| **Nantes Métropole** | 3 | 3 162 | 1 787 | 1 061 | 161 | 264 | 107 | 32 | 774 |
| **Bordeaux Métropole** | 9 | 3 159 | 2 157 | 530 | 129 | 505 | 134 | 27 | 793 |
| **Montpellier Méditerranée Métropole** | 5 | 2 805 | 1 447 | 775 | 169 | 207 | 59 | 15 | 496 |
| **CU du Grand Poitiers** | 5 | 2 666 | 887 | 1 126 | 83 | 269 | 116 | 34 | 430 |
| **Brest Métropole** | 4 | 1 194 | 746 | 313 | 45 | 153 | 29 | 8 | 117 |
| **CA du Pays Basque** | 7 | 3 902 | 1 047 | 1 649 | 142 | 518 | 72 | 22 | 625 |
| **Le Havre Seine Métropole** | 4 | 1 711 | 844 | 676 | 83 | 1 737 | 67 | 15 | 672 |
| **CA Lorient Agglomération** | 9 | 2 141 | 965 | 875 | 64 | 184 | 52 | 12 | 143 |
| **CA de Châlons-en-Champagne** | 7 | 1 554 | 464 | 812 | 93 | 396 | 34 | 13 | 365 |
| **Ardenne Métropole** | 4 | 1 776 | 286 | 413 | 95 | 220 | 79 | 16 | 423 |
| **CA du Cotentin** | 6 | 2 559 | 889 | 1 035 | 51 | 286 | 58 | 14 | 217 |
| **CA Montélimar Agglomération** | 5 | 967 | 355 | 532 | 51 | 142 | 91 | 16 | 456 |
| **CU de Dunkerque** | 4 | 1 357 | 380 | 454 | 101 | 901 | 105 | 24 | 1 151 |
| **CA du Grand Verdun** | 2 | 730 | 153 | 287 | 34 | 130 | 9 | 3 | 80 |
| **CA du Pays de Saint Malo Agglom.** | 3 | 915 | 342 | 414 | 33 | 81 | 32 | 7 | 75 |
| **CA du Boulonnais** | 4 | 760 | 320 | 276 | 46 | 90 | 19 | 6 | 153 |
| **CA du Pays Ajaccien** | 5 | 742 | 165 | 161 | 6 | 190 | 15 | 5 | 84 |
| **CC de Cattenom et Environs** | 2 | 599 | 84 | 296 | 17 | 37 | 10 | 3 | 95 |
| **CA Grand Calais Terres et Mers** | 5 | 701 | 393 | 245 | 60 | 80 | 36 | 10 | 393 |
| **CA du Pays de Meaux** | 4 | 1 029 | 327 | 247 | 39 | 170 | 26 | 9 | 183 |
| **CC de l'Île de Ré** | 0 | 931 | 143 | 56 | 1 | 13 | 1 | 1 | 0 |

### 3.4 Réseau routier (troncon_de_route) par EPCI

| EPCI | Total | Autoroute | Route 2ch | Route 1ch | Bretelle | Chemin | Sentier | Imp≤3 | Restr. poids | Restr. hauteur | Urbain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Métropole du Grand Paris** | 355 897 | 2 505 | 17 056 | 246 259 | 2 756 | 5 030 | 57 072 | 46 907 | 4 482 | 4 032 | 341 201 |
| **Métropole d'Aix-Marseille-Provence** | 369 265 | 2 140 | 5 893 | 179 730 | 1 254 | 66 569 | 45 608 | 25 544 | 1 182 | 2 640 | 232 040 |
| **Métropole de Lyon** | 139 249 | 1 277 | 3 750 | 97 388 | 1 062 | 7 477 | 14 204 | 15 911 | 1 082 | 1 553 | 120 278 |
| **CU du Grand Reims** | 137 681 | 510 | 1 001 | 58 777 | 319 | 37 663 | 26 796 | 7 749 | 201 | 204 | 69 549 |
| **Nantes Métropole** | 141 930 | 841 | 2 050 | 89 442 | 557 | 12 357 | 17 932 | 13 065 | 1 235 | 523 | 112 607 |
| **Toulouse Métropole** | 136 053 | 790 | 3 312 | 101 858 | 633 | 5 064 | 10 555 | 10 110 | 172 | 913 | 123 288 |
| **Métropole Européenne de Lille** | 107 657 | 750 | 3 900 | 77 953 | 852 | 4 033 | 10 855 | 12 695 | 1 510 | 830 | 96 353 |
| **Bordeaux Métropole** | 104 377 | 382 | 3 556 | 70 830 | 439 | 9 869 | 6 795 | 10 331 | 13 | 35 | 90 018 |
| **Montpellier Méditerranée Métropole** | 100 101 | 554 | 2 792 | 58 437 | 464 | 12 754 | 13 687 | 6 751 | 25 | 265 | 69 051 |
| **CA du Pays Basque** | 126 979 | 475 | 867 | 73 905 | 220 | 23 293 | 13 720 | 11 922 | 180 | 260 | 55 828 |
| **CU du Grand Poitiers** | 119 075 | 360 | 1 207 | 66 323 | 289 | 21 748 | 6 186 | 8 355 | 24 | 180 | 53 496 |
| **Eurométropole de Strasbourg** | 73 068 | 494 | 2 944 | 47 180 | 526 | 7 692 | 7 830 | 9 076 | 233 | 275 | 57 154 |
| **Grenoble-Alpes-Métropole** | 69 699 | 402 | 2 039 | 42 452 | 338 | 7 066 | 11 193 | 6 796 | 1 713 | 458 | 48 224 |
| **Métropole Rouen Normandie** | 88 722 | 574 | 2 239 | 55 042 | 301 | 9 106 | 12 689 | 8 014 | 92 | 490 | 65 374 |
| **CA du Cotentin** | 65 800 | 134 | 772 | 38 664 | 157 | 8 701 | 6 845 | 6 274 | 29 | 33 | 29 763 |
| **CA de Châlons-en-Champagne** | 59 466 | 442 | 254 | 24 108 | 227 | 17 184 | 7 034 | 4 539 | 7 | 50 | 27 101 |
| **CA Lorient Agglomération** | 81 712 | 217 | 785 | 48 938 | 164 | 10 802 | 11 262 | 7 366 | 0 | 6 | 42 740 |
| **Ardenne Métropole** | 50 024 | 465 | 185 | 21 224 | 196 | 10 254 | 12 008 | 3 330 | 27 | 34 | 24 923 |
| **Le Havre Seine Métropole** | 41 273 | 296 | 1 136 | 27 922 | 281 | 2 444 | 3 779 | 4 314 | 43 | 184 | 30 380 |
| **CA Montélimar Agglomération** | 40 019 | 130 | 529 | 19 709 | 58 | 7 961 | 5 279 | 2 958 | 24 | 72 | 15 311 |
| **CU de Dunkerque** | 34 195 | 261 | 888 | 23 969 | 251 | 1 236 | 3 928 | 3 106 | 68 | 170 | 26 841 |
| **CA du Pays de Saint Malo Agglom.** | 27 396 | 204 | 388 | 18 961 | 131 | 1 648 | 2 678 | 2 876 | 41 | 65 | 19 375 |
| **CA du Pays Ajaccien** | 23 691 | 0 | 305 | 10 653 | 4 | 4 292 | 4 746 | 1 904 | 0 | 11 | 11 787 |
| **CA du Grand Verdun** | 21 268 | 63 | 163 | 7 613 | 17 | 3 759 | 4 926 | 1 865 | 4 | 19 | 8 498 |
| **CA du Pays de Meaux** | 19 933 | 87 | 617 | 11 432 | 58 | 2 309 | 2 885 | 2 102 | 655 | 112 | 14 177 |
| **CA du Boulonnais** | 17 567 | 171 | 272 | 10 705 | 96 | 1 136 | 2 894 | 1 953 | 37 | 108 | 12 001 |
| **CC de l'Île de Ré** | 13 190 | 0 | 114 | 7 494 | 0 | 2 809 | 1 583 | 706 | 0 | 0 | 7 739 |
| **CA Grand Calais Terres et Mers** | 15 553 | 263 | 392 | 10 197 | 163 | 1 007 | 1 458 | 2 278 | 279 | 128 | 11 308 |
| **CC de Cattenom et Environs** | 10 578 | 38 | 79 | 5 641 | 12 | 2 279 | 1 306 | 975 | 48 | 9 | 5 382 |
| **Brest Métropole** | 38 077 | 113 | 1 085 | 25 008 | 91 | 1 952 | 5 331 | 4 155 | 14 | 69 | 31 726 |

---

## 4. Mapping rôles → tables + filtres (validé)

### Rôle ATTAQUE

**Objectif** : Identifier les cibles stratégiques à neutraliser.

| Table | Filtre | POIs obtenus | Exemple Brest |
|---|---|---|---|
| `aerodrome` | `categorie IN ('Internationale','Nationale')` | Aérodromes majeurs | 1 |
| `equipement_de_transport` | `nature='Port' AND nature_detaillee='Port de commerce'` | Ports commerciaux | 1 |
| `zone_d_activite_ou_d_interet` | `categorie='Administratif ou militaire' AND nature IN ('Gendarmerie','Caserne','Camp militaire non clos')` | Casernes, gendarmeries | ~5 |
| `construction_ponctuelle` | `nature='Tour de contrôle aérien'` | Tours de contrôle | ~0-1 |

### Rôle DÉFENSE

**Objectif** : Identifier les points à protéger.

| Table | Filtre | POIs obtenus |
|---|---|---|
| `zone_d_activite_ou_d_interet` | `nature IN ('Hôpital','Établissement hospitalier','Maison de retraite')` | Hôpitaux, EHPAD |
| `zone_d_activite_ou_d_interet` | `categorie='Administratif ou militaire' AND nature IN ('Gendarmerie','Caserne')` | Forces de l'ordre |
| `equipement_de_transport` | `nature LIKE 'Gare%'` | Gares (évacuation) |
| `construction_ponctuelle` | `nature IN ('Phare','Tour de guet')` | Points d'observation |
| `construction_surfacique` | `nature='Pont'` | Ponts stratégiques |

### Rôle RAVITAILLEMENT

**Objectif** : Optimiser les flux logistiques.

| Table | Filtre | POIs obtenus |
|---|---|---|
| `equipement_de_transport` | `nature IN ('Port') AND nature_detaillee IN ('Port de commerce','Port de pêche','Halte fluviale')` | Ports |
| `equipement_de_transport` | `nature IN ('Gare fret uniquement','Gare voyageurs et fret')` | Gares fret |
| `zone_d_activite_ou_d_interet` | `nature IN ('Zone industrielle','Zone d\'activités','Usine','Marché')` | Zones logistiques |
| `reservoir` | `nature='Réservoir industriel'` | Réservoirs |
| `troncon_de_voie_ferree` | `usage='Fret'` | Voies ferrées fret |

### Rôle ÉNERGIE

**Objectif** : Sécuriser le réseau énergétique.

| Table | Filtre | POIs obtenus |
|---|---|---|
| `poste_de_transformation` | `CAST(importance AS INTEGER) <= 3` | Postes critiques (1-3) |
| `ligne_electrique` | `voltage IN ('400 kV','225 kV')` | Lignes THT |
| `construction_ponctuelle` | `nature IN ('Éolienne','Transformateur','Cheminée')` | Sources d'énergie |
| `construction_surfacique` | `nature='Barrage'` | Barrages hydro |
| `canalisation` | `nature='Hydrocarbures'` | Oléoducs/gazoducs |
| `reservoir` | `nature='Réservoir industriel'` | Stockage énergie |

### Rôle INDUSTRIES

**Objectif** : Identifier les complexes industriels à cibler/protéger.

| Table | Filtre | POIs obtenus |
|---|---|---|
| `zone_d_activite_ou_d_interet` | `categorie='Industriel et commercial' AND nature IN ('Zone industrielle','Usine','Déchèterie','Divers industriel')` | Zones industrielles |
| `construction_ponctuelle` | `nature IN ('Puits de pétrole','Puits de gaz','Torchère','Cheminée')` | Installations lourdes |
| `construction_lineaire` | `nature='Portique portuaire'` | Portiques (fret maritime) |
| `equipement_de_transport` | `nature='Port' AND nature_detaillee IN ('Port de commerce','Bassin')` | Ports industriels |

---

## 5. Points d'attention pour le TD

### 5.1 EPCIs trop grands / trop petits
- **Grand Paris** (356k routes, 24k POIs) : trop lourd pour un TD. Risque timeouts pgRouting.
- **Île de Ré / Cattenom** (< 15k routes, < 1k POIs) : très rapide mais peut manquer de profondeur.
- **Sweet spot** : 30k-140k routes (Brest, Dunkerque, Le Havre, Grenoble, Nantes, Toulouse, Lille, Bordeaux).

### 5.2 Spécificités notables
- **Le Havre** : 1 737 réservoirs (port pétrolier !) → parfait rôle Énergie.
- **Dunkerque** : 901 réservoirs + 1 151 voies ferrées → parfait rôle Industries/Ravitaillement.
- **Grand Paris** : 4 482 restrictions de poids → excellent pour routage contraint.
- **Pays Basque** : 23k chemins + 13k sentiers → terrain montagneux, routage intéressant.
- **Cotentin** : péninsule, peu de routes alternatives → choke points évidents.
- **Île de Ré** : 0 gares, 0 aérodromes → rôle Défense ou Ravitaillement maritime uniquement.
- **Ajaccien** : 0 autoroute → pas de réseau高速.
- **Grenoble** : cuvette, 1 713 restrictions de poids → zone montagneuse.

### 5.3 Centrales nucléaires (non dans BDTOPO)
Les centrales ne sont pas des POI BDTOPO. Pour les rôles Énergie, on peut :
1. Injecter des POIs custom (coords approximatives) lors du setup
2. Ou utiliser uniquement les infractions BDTOPO réelles (postes THT, barrages, etc.)

Recommandation : injecter 15 centrales comme `zone_d_activite` custom dans le setup.
