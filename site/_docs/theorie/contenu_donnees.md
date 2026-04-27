---
layout: default
title: Contenu des données BDTOPO
parent: Théorie
nav_order: 2
---

> Statistiques par EPCI et graphiques générés par `scripts/generate_theory_stats.py` depuis `data/epci_extracts/`.
> Pour ajouter ou retirer un EPCI : modifier le dict `EPCIS` en haut du script et relancer `uv run python scripts/generate_theory_stats.py`.

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

## 3. EPCIs sélectionnés (13)

### 3.1 Critères de sélection

Les 13 EPCIs sont choisis pour maximiser la **diversité géographique et thématique** :
- **Métropoles littorales** : Brest, Le Havre, Bordeaux, Nantes, Rouen
- **Frontières** : Strasbourg (Allemagne), Lille (Belgique), Dunkerque (Belgique + nucléaire), Pays Basque (Espagne)
- **Montagne / cuvette** : Grenoble, Pays Basque
- **Péninsules** : Brest, Cotentin (avec nucléaire Flamanville)
- **Métropoles intérieures** : Lyon, Tours
- Taille variée : de Dunkerque (~34k routes) à Nantes (~142k routes)

### 3.2 Centrales nucléaires proches

Les centrales ne sont PAS dans BDTOPO. Coordonnées approximatives utilisées :

| Centrale | Coords | EPCI le plus proche |
|---|---|---|
| Gravelines | (2.14, 51.0) | CU de Dunkerque |
| Flamanville | (-1.85, 49.55) | CA du Cotentin |

### 3.3 Matrice POI par EPCI

| EPCI | aérod. | zone_act. | eq_transp | constr_ponct. | constr_surf. | réservoir | ligne_élec. | poste_transf. | voie_ferrée |
|---|---|---|---|---|---|---|---|---|---|
| **Brest** | 4 | 1 194 | 746 | 313 | 45 | 153 | 29 | 8 | 117 |
| **Le Havre** | 4 | 1 711 | 844 | 676 | 83 | 1 737 | 67 | 15 | 672 |
| **Dunkerque** | 4 | 1 357 | 380 | 454 | 101 | 901 | 105 | 24 | 1 151 |
| **Cotentin** | 6 | 2 559 | 889 | 1 035 | 51 | 286 | 58 | 14 | 217 |
| **Grenoble** | 11 | 2 706 | 1 204 | 781 | 110 | 526 | 147 | 25 | 515 |
| **Strasbourg** | 7 | 3 284 | 1 408 | 738 | 282 | 438 | 99 | 19 | 1 568 |
| **Lille** | 6 | 5 208 | 2 405 | 1 350 | 185 | 498 | 112 | 30 | 789 |
| **Pays Basque** | 7 | 3 902 | 1 047 | 1 649 | 142 | 518 | 72 | 22 | 625 |
| **Rouen** | 7 | 3 553 | 1 662 | 882 | 132 | 816 | 130 | 30 | 1 330 |
| **Bordeaux** | 9 | 3 159 | 2 157 | 530 | 129 | 505 | 134 | 27 | 793 |
| **Nantes** | 3 | 3 162 | 1 787 | 1 061 | 161 | 264 | 107 | 32 | 774 |
| **Lyon** | 11 | 7 304 | 2 572 | 1 535 | 271 | 960 | 232 | 46 | 2 987 |
| **Tours** | 4 | 2 094 | 996 | 445 | 120 | 201 | 75 | 11 | 647 |

### 3.4 Réseau routier (troncon_de_route) par EPCI

| EPCI | Total | Autoroute | Route 2ch | Route 1ch | Bretelle | Chemin | Sentier | Imp≤3 | Restr. poids | Restr. hauteur | Urbain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Brest** | 38 074 | 113 | 1 085 | 25 006 | 91 | 1 952 | 5 330 | 4 155 | 14 | 69 | 31 723 |
| **Le Havre** | 41 272 | 296 | 1 136 | 27 921 | 281 | 2 444 | 3 779 | 4 314 | 43 | 184 | 30 380 |
| **Dunkerque** | 34 195 | 261 | 888 | 23 969 | 251 | 1 236 | 3 928 | 3 106 | 68 | 170 | 26 841 |
| **Cotentin** | 65 800 | 134 | 772 | 38 664 | 157 | 8 701 | 6 845 | 6 274 | 29 | 33 | 29 763 |
| **Grenoble** | 69 698 | 402 | 2 039 | 42 452 | 338 | 7 066 | 11 192 | 6 796 | 1 713 | 458 | 48 224 |
| **Strasbourg** | 73 067 | 494 | 2 944 | 47 180 | 526 | 7 691 | 7 830 | 9 076 | 233 | 275 | 57 154 |
| **Lille** | 107 657 | 750 | 3 900 | 77 953 | 852 | 4 033 | 10 855 | 12 695 | 1 510 | 830 | 96 353 |
| **Pays Basque** | 126 976 | 475 | 867 | 73 903 | 220 | 23 293 | 13 720 | 11 922 | 180 | 260 | 55 827 |
| **Rouen** | 88 720 | 574 | 2 239 | 55 042 | 301 | 9 104 | 12 689 | 8 014 | 92 | 490 | 65 373 |
| **Bordeaux** | 104 377 | 382 | 3 556 | 70 830 | 439 | 9 869 | 6 795 | 10 331 | 13 | 35 | 90 018 |
| **Nantes** | 141 928 | 841 | 2 050 | 89 442 | 557 | 12 357 | 17 931 | 13 065 | 1 235 | 523 | 112 605 |
| **Lyon** | 139 248 | 1 277 | 3 749 | 97 388 | 1 062 | 7 477 | 14 204 | 15 910 | 1 082 | 1 553 | 120 277 |
| **Tours** | 58 077 | 508 | 1 657 | 35 572 | 310 | 6 237 | 7 189 | 5 134 | 302 | 339 | 43 063 |

### 3.5 Visualisations

Les graphiques ci-dessous complètent les tableaux : ils permettent de comparer visuellement les EPCIs et de comprendre d'un coup d'œil les ressources disponibles par rôle.

#### Répartition des POIs par type (vue consolidée)

![POI counts]({{ "/assets/img/theory/chart_poi_counts.png" | relative_url }})

**Ce graphe montre** le nombre de POIs par catégorie pour chaque EPCI. Lyon domine sur presque tous les types (11 millions d'habitants). Brest, Dunkerque et Le Havre se distinguent sur les équipements de transport (ports, marinas). Grenoble et Lyon trustent les constructions linéaires (tunnels, viaducs alpins).

#### Réseau routier : urbanisation vs rural

![Road network]({{ "/assets/img/theory/chart_road_network.png" | relative_url }})

**Deux couleurs** : bleu = tronçons en zone urbaine, orange = rural. Les EPCIs métropoles (Lyon, Lille, Bordeaux) ont un réseau quasi-intégralement urbain. Le Cotentin et le Pays Basque sont profondément ruraux. Useful pour le TD ravitaillement : les livraisons en zone rurale dépendent des chemins (plus lents, plus vulnérables).

#### Chaleur : alignment des rôles

![Role heatmap]({{ "/assets/img/theory/chart_role_heatmap.png" | relative_url }})

**Lignes** = rôles (Attaque, Défense, Ravitaillement, Énergie). **Couleurs** = pertinence des tables pour ce rôle (échelle log). Un coefficient élevé (rouge) signifie que cette table contient beaucoup de POIs utiles à ce rôle dans la majorité des EPCIs. Par exemple : Ravitaillement → `reservoir` (eau potable, industiel) est pertinent partout.

#### Composition du réseau routier par type de voie

![Road composition]({{ "/assets/img/theory/chart_road_composition.png" | relative_url }})

**Barres empilées** : autoroute (foncé) / 2 canaux (medium) / 1 canal (clair) / chemins & autres (très clair). Permet d'évaluer la capacité de déplacement rapide : un EPCI avec beaucoup d'orange clair = réseau sparse, temps de trajet plus longs. Bordeaux et Lille ont la meilleure densité autoroutière.

#### Inventaire global des données (par table)

![Data inventory]({{ "/assets/img/theory/chart_data_inventory.png" | relative_url }})

**Totaux agrégés sur les 13 EPCIs** pour chaque table source. `troncon_de_route` domine (~1,5 million de segments routiers). `construction_lineaire` et `construction_ponctuelle` sont les deuxièmes postes. Utile pour comprendre le poids de chaque table dans les requêtes JOIN.

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
