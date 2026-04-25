# Rôle RAVITAILLEMENT

> *"Optimiser les flux logistiques et les chaînes d'approvisionnement."*

## Objectif

Localiser les nœuds logistiques critiques (ports, gares fret, zones industrielles).

## Tables BDTOPO à interroger

| Table | Filtre | Type de POI |
|-------|--------|-------------|
| `equipement_de_transport` | `nature = 'Port' AND nature_detaillee IN ('Port de commerce', 'Port de pêche', 'Halte fluviale')` | Ports |
| `equipement_de_transport` | `nature IN ('Gare fret uniquement', 'Gare voyageurs et fret')` | Gares fret |
| `zone_d_activite_ou_d_interet` | `nature IN ('Zone industrielle', 'Zone d''activités', 'Usine', 'Marché')` | Zones logistiques |
| `reservoir` | `nature = 'Réservoir industriel'` | Stockage |

## Requête de base

```sql
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'ravitaillement', 'port', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
FROM equipement_de_transport
WHERE nature = 'Port' AND nature_detaillee IN ('Port de commerce', 'Port de pêche', 'Halte fluviale');
```

## Contrainte routage (Phase 2)

**Poids lourds** : bloquer les routes avec restrictions de poids.

```sql
CASE WHEN restriction_de_poids_total IS NOT NULL THEN -1 ELSE cost END
```

## Indice Codestral

```
"Trouve les ports de commerce, gares fret et zones industrielles
dans l'EPCI. Filtre les réservoirs industriels.
Exclus les routes avec restriction_de_poids_total pour le routage."
```
