---
title: Énergie
parent: Rôles
nav_order: 4
layout: default
---
# ⚡ Rôle ÉNERGIE

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

## Questions bonus (Phase 1 — Exploration libre)

Résolvez au moins 2 de ces questions. Documentez vos requêtes.

### B1 — Postes HT et hôpitaux : qui dépend de qui ?

> Quels postes de transformation critiques (importance ≤ 3) sont à moins de 1 km d'un hôpital ?

*Indice : joignez `poste_de_transformation` et `zone_d_activite_ou_d_interet` avec `ST_DWithin`, rayon 1000m, filtrez `CAST(importance AS INTEGER) <= 3`.*

**Question** : si ce poste tombe, quel hôpital est touché ? (début de la simulation Phase 3).

### B2 — Lignes THT : quelles routes croisent-elles ?

> Combien de routes sont croisées par une ligne 400 kV ? Ce sont des points de fragilité.

*Indice : joignez `ligne_electrique` et `troncon_de_route` via `ST_Intersects`, filtrez `voltage IN ('400 kV', '225 kV')`.*

**Variante** : parmi ces routes, combien sont d'importance ≤ 2 ?

### B3 — Centrales nucléaires : rayon d'influence

> Dans un rayon de 20 km autour de chaque centrale, combien de POIs de chaque rôle ?

*Indice : joignez `mission_custom_pois` et `mission_pois` avec `ST_DWithin`, rayon 20000m.*

### B4 — Mix énergétique de l'EPCI

> Comptez les éoliennes, barrages, transformateurs et centrales. Quelle est la répartition ?

*Indice : 4 `SELECT ... UNION ALL` — un par source (`construction_ponctuelle`, `construction_surfacique`, `poste_de_transformation`, `mission_custom_pois`).*

→ [Corrigé]({% link _docs/corriges/corrige_roles_bonus.md %}#-nergie)

---

## Indice Codestral

```
"Trouve les postes de transformation critiques (importance <= 3),
les lignes THT (400kV, 225kV), les éoliennes, barrages et oléoducs.
Inclus aussi les centrales nucléaires de la table mission_custom_pois."
```
