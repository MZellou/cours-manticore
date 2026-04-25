---
title: Défense
---
# Rôle DÉFENSE

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

## Indice Codestral

```
"Trouve tous les hôpitaux, casernes de gendarmerie, gares et ponts
dans l'EPCI. Combine plusieurs tables avec UNION ALL et filtre
par jointure spatiale avec le polygone EPCI."
```
