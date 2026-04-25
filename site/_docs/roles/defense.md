---
title: Défense
parent: Rôles
nav_order: 2
layout: default
---
# 🛡️ Rôle DÉFENSE

> *"Identifier les points à protéger et les voies d'évacuation."*

## Objectif

Localiser les infrastructures vitales dont la perte affecterait la population.

## Tables BDTOPO à interroger

| Table | Filtre | Type de POI |
|-------|--------|-------------|
| `zone_d_activite_ou_d_interet` | `nature IN ('Hôpital', 'Établissement hospitalier', 'Maison de retraite')` | Santé |
| `zone_d_activite_ou_d_interet` | `categorie = 'Administratif ou militaire' AND nature IN ('Gendarmerie', 'Caserne')` | Sécurité |
| `equipement_de_transport` | `nature ILIKE 'Gare%'` | Évacuation |
| `construction_surfacique` | `nature = 'Pont'` | Infrastructures clés |
| `construction_ponctuelle` | `nature IN ('Phare', 'Tour de guet')` | Observation |

## Requête de base

```sql
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'defense', 'hopital', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
FROM zone_d_activite_ou_d_interet
WHERE nature IN ('Hôpital', 'Établissement hospitalier', 'Maison de retraite');
```

## Contrainte routage (Phase 2)

**Rapidité** : prioriser les grands axes (autoroutes, routes importance >= 3).

```sql
CASE WHEN importance >= 3 OR nature = 'Autoroute' THEN cost * 0.5 ELSE cost END
```

## Questions bonus (Phase 1 — Exploration libre)

Résolvez au moins 2 de ces questions. Documentez vos requêtes.

### B1 — Hôpitaux et gares : réseau d'évacuation

> Quels hôpitaux sont à moins de 1 km d'une gare (évacuation ferroviaire) ?

*Indice : joignez `zone_d_activite_ou_d_interet` (hôpitaux) et `equipement_de_transport` (gares) avec `ST_DWithin`, rayon 1000m.*

**Variante** : et les hôpitaux SANS gare à moins de 1 km ? (indice : `NOT EXISTS` ou `LEFT JOIN ... WHERE g.id IS NULL`)

### B2 — Ponts critiques sur les axes principaux

> Combien de ponts sont sur des routes d'importance ≤ 2 (nationales) ?

*Indice : joignez `construction_surfacique` (nature='Pont') avec `troncon_de_route` via `ST_Intersects`, filtrez `CAST(importance AS INTEGER) <= 2`.*

### B3 — Buffer de sécurité autour des hôpitaux

> Combien de POIs d'autres rôles tombent dans un rayon de 500m autour d'un hôpital ?

*Indice : CTE avec `ST_Buffer(geometrie, 500)`, puis jointure avec `mission_pois` via `ST_Intersects`, filtrez `role != 'defense'`.*

### B4 — Densité de forces de l'ordre par zone

> Quel est le ratio gendarmerie / caserne par km² dans votre EPCI ?

*Indice : comptez les gendarmeries + casernes, divisez par `ST_Area` du polygone EPCI.*

→ [Corrigé]({% link _docs/corriges/corrige_roles_bonus.md %}#-dfense)

---

## Indice Codestral

```
"Trouve tous les hôpitaux, casernes de gendarmerie, gares et ponts
dans l'EPCI. Combine plusieurs tables avec UNION ALL et filtre
par jointure spatiale avec le polygone EPCI."
```
