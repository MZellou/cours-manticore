# Rôle ÉNERGIE

> *"Sécuriser le réseau énergétique et les infrastructures de production."*

## Objectif

Localiser les infrastructures critiques de production et de transport d'énergie.

## Tables BDTOPO à interroger

| Table | Filtre | Type de POI |
|-------|--------|-------------|
| `poste_de_transformation` | `CAST(importance AS INTEGER) <= 3` | Postes critiques |
| `ligne_electrique` | `voltage IN ('400 kV', '225 kV')` | Lignes THT |
| `construction_ponctuelle` | `nature IN ('Éolienne', 'Transformateur', 'Cheminée')` | Sources d'énergie |
| `construction_surfacique` | `nature = 'Barrage'` | Hydroélectricité |
| `canalisation` | `nature = 'Hydrocarbures'` | Oléoducs/gazoducs |
| `mission_custom_pois` | *(toutes)* | **Centrales nucléaires** (injectées au setup) |

## Requête de base

```sql
-- Postes de transformation critiques
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'energie', 'poste_ht', cleabs, nature, CAST(importance AS INTEGER)::TEXT, NULL, ST_Force2D(geometrie)
FROM poste_de_transformation WHERE CAST(importance AS INTEGER) <= 3;

-- Centrales nucléaires (injectées par le setup)
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'energie', 'centrale', id::TEXT, type, puissance_mw::TEXT, nom, geometrie
FROM mission_custom_pois;
```

## Contrainte routage (Phase 2)

**Convois exceptionnels** : exclure les routes étroites (< 4m).

```sql
CASE WHEN largeur_de_chaussee >= 4 OR largeur_de_chaussee IS NULL THEN cost ELSE -1 END
```

## Indice Codestral

```
"Trouve les postes de transformation critiques (importance <= 3),
les lignes THT (400kV, 225kV), les éoliennes, barrages et oléoducs.
Inclus aussi les centrales nucléaires de la table mission_custom_pois."
```
