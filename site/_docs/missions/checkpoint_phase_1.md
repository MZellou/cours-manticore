---
title: Checkpoint Phase 1
parent: Missions
nav_order: 3
layout: default
---

# ✅ Checkpoint Phase 1 → Phase 2

> *Sanity check avant de passer à la cartographie.*
> Si quelque chose cloche ici, **ne passez pas en Phase 2** : le débogage sera 10× plus pénible quand le graphe sera mêlé à l'affaire.

---

## 1. La table `mission_pois` existe et a les 4 rôles

```sql
SELECT role, count(*) AS nb_pois
FROM mission_pois
GROUP BY role
ORDER BY role;
```

**Attendu** :

| Symptôme | Diagnostic |
|----------|------------|
| 4 lignes (attaque, défense, énergie, ravitaillement), `nb_pois > 0` partout | ✅ OK, passez à la suite |
| Moins de 4 rôles | ⚠️ Au moins un agent n'a pas exécuté son `INSERT INTO mission_pois`. Le récupérer. |
| Tous les rôles à 0 | ❌ Aucun agent n'a inséré. Recommencez à T2. |

### Fourchettes attendues par rôle (ordre de grandeur)

Variable selon l'EPCI, mais **si vous êtes très en-dessous, il y a probablement un filtre trop strict** :

| Rôle | EPCI petit (~30 k routes) | EPCI moyen (~80 k routes) | EPCI grand (~140 k routes) |
|------|---------------------------|---------------------------|----------------------------|
| Attaque | 5–30 | 20–80 | 50–200 |
| Défense | 10–50 | 30–150 | 80–300 |
| Ravitaillement | 5–40 | 20–100 | 50–250 |
| Énergie | 10–80 | 40–200 | 100–400 |

> Si vous obtenez **0 ou très peu**, vérifiez :
> - Le **SRID** des géométries (`SELECT ST_SRID(geom) FROM mission_pois LIMIT 1` → doit être `2154`).
> - Que vous filtrez bien sur **votre EPCI** et pas sur toute la France.
> - Que les filtres `categorie` / `nature` correspondent aux **valeurs réelles** dans la table source (`SELECT DISTINCT nature FROM zone_d_activite_ou_d_interet WHERE …`).

---

## 2. Les sources de POI sont multiples (pas qu'une seule table)

```sql
SELECT role, source, count(*)
FROM mission_pois
GROUP BY role, source
ORDER BY role, count DESC;
```

Chaque rôle devrait avoir **au moins 2 sources** (selon votre [briefing rôle]({% link _docs/roles.md %})). Si tout est dans une seule table, vous avez raté une partie de la mission.

---

## 3. Les géométries sont valides et en SRID 2154

```sql
SELECT
  count(*) FILTER (WHERE NOT ST_IsValid(geom)) AS invalid,
  count(*) FILTER (WHERE ST_SRID(geom) <> 2154) AS bad_srid,
  count(*) FILTER (WHERE geom IS NULL) AS null_geom
FROM mission_pois;
```

→ **Tous les compteurs doivent être à 0.** Sinon, débogage avant Phase 2.

---

## 4. L'index spatial existe

```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'mission_pois' AND indexdef LIKE '%gist%';
```

→ Au moins un index GIST. Sinon :

```sql
CREATE INDEX IF NOT EXISTS idx_mission_pois_geom ON mission_pois USING GIST (geom);
```

> Sans cet index, la Phase 2 (snap des POIs aux sommets du graphe) sera **catastrophiquement lente**.

---

## 5. (Optionnel) Le clustering DBSCAN a produit du sens

```sql
SELECT
  ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cluster_id,
  count(*) AS nb_pois
FROM mission_pois
WHERE role = 'votre_role'
GROUP BY cluster_id
ORDER BY cluster_id NULLS LAST;
```

| Symptôme | Diagnostic |
|----------|------------|
| 2–8 clusters + un peu de bruit (`NULL`) | ✅ Bon équilibre |
| Tout dans `NULL` | ⚠️ `eps` trop petit ou POIs très dispersés — essayez `eps = 5000` |
| 1 seul gros cluster | ⚠️ `eps` trop grand — essayez `eps = 1000` |

---

## 6. Auto-validation : ce que vous savez expliquer

Avant de passer en Phase 2, vous devriez pouvoir **répondre sans LLM** :

- Pourquoi BDTOPO est en SRID 2154 et pas 4326
- Différence `ST_Intersects` / `ST_DWithin` / `ST_Distance`
- Pourquoi un index GIST est nécessaire
- Effet de `eps` et `minpoints` sur DBSCAN
- Quels filtres de votre rôle sélectionnent quels POIs

> Si une de ces questions vous bloque : **dialoguez avec le LLM** sur cette question avant la Phase 2.

---

{% include nav_phase.html prev_url="/missions/phase_1_reconnaissance/" prev_label="Phase 1" next_url="/missions/transition_1_2/" next_label="Transition 1→2" %}
