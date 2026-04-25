---
title: Attaque
parent: Rôles
nav_order: 1
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

## Indice Codestral

```
"Trouve tous les aérodromes internationaux et nationaux dans l'EPCI,
ainsi que les ports de commerce et les casernes militaires.
Utilise des UNION ALL pour combiner les sources."
```
