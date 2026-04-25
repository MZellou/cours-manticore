---
title: Attaque
parent: Rôles
nav_order: 1
layout: default
---
# ⚔️ Rôle ATTAQUE

> *"Identifier les cibles stratégiques à neutraliser."*

## Objectif

Localiser les infrastructures dont la destruction maximiserait l'impact sur l'EPCI.

## Tables BDTOPO à interroger

| Table | Filtre | Type de POI |
|-------|--------|-------------|
| `aerodrome` | `categorie IN ('Internationale', 'Nationale')` | Aérodromes majeurs |
| `equipement_de_transport` | `nature = 'Port' AND nature_detaillee = 'Port de commerce'` | Ports commerciaux |
| `zone_d_activite_ou_d_interet` | `categorie = 'Administratif ou militaire' AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')` | Forces armées |
| `construction_ponctuelle` | `nature ILIKE 'Tour de contrôle%'` | Tours de contrôle |

## Requête de base

```sql
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'attaque', 'aerodrome', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
FROM aerodrome WHERE categorie IN ('Internationale', 'Nationale');
```

## Contrainte routage (Phase 2)

**Discrétion** : favoriser les routes secondaires (chemins, sentiers) et pénaliser les grands axes.

```sql
CASE WHEN nature IN ('Chemin', 'Sentier') THEN cost * 0.7 ELSE cost * 1.3 END
```

## Questions bonus (Phase 1 — Exploration libre)

Résolvez au moins 2 de ces questions. Documentez vos requêtes.

### B1 — Couverture aérienne

> Combien de ports sont à moins de 5 km d'un aérodrome international/national ?

*Indice : joignez `aerodrome` et `equipement_de_transport` avec `ST_DWithin`, filtrez les catégories d'aérodromes et `nature = 'Port'`.*

**Variante** : et dans un rayon de 10 km ? 20 km ? Tracez la courbe.

### B2 — Forces militaires par cluster

> Utilisez ST_ClusterDBSCAN sur les gendarmeries et casernes. Où sont les concentrations ?

*Indice : CTE avec filtre `categorie = 'Administratif ou militaire'`, puis `ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER()`.*

### B3 — Tour de contrôle vs aérodromes

> Chaque aérodrome majeur a-t-il une tour de contrôle à proximité ?

*Indice : sous-requête corrélée dans le SELECT — comptez les `construction_ponctuelle` avec `nature ILIKE 'Tour de contrôle%'` à moins de 1 km.*

### B4 — Vitesse d'accès aux cibles

> Quelle est la vitesse moyenne des routes à moins de 2 km de chaque cible ?

*Indice : joignez `mission_pois` (role='attaque') avec `troncon_de_route` via `ST_DWithin` et faites `avg(vitesse_moyenne_vl)`.*

→ [Corrigé]({% link _docs/corriges/corrige_roles_bonus.md %}#-attaque)

---

## Indice Codestral

```
"Trouve tous les aérodromes internationaux et nationaux dans l'EPCI,
ainsi que les ports de commerce et les casernes militaires.
Utilise des UNION ALL pour combiner les sources."
```
