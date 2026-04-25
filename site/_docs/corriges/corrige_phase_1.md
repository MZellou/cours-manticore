---
title: Corrigé Phase 1
parent: Corrigés
nav_order: 1
layout: default
---
# Corrigé Phase 1 — Reconnaissance

> Solutions des exercices. Cliquez pour révéler.

---

## T0a — SQL : GROUP BY, HAVING, ORDER BY

<details>
<summary>Solution</summary>

```sql
-- Combien d'entrées par catégorie ?
SELECT categorie, count(*) AS nb
FROM zone_d_activite_ou_d_interet
GROUP BY categorie
ORDER BY nb DESC;

-- Quelles catégories ont plus de 10 000 entrées ?
SELECT categorie, count(*) AS nb
FROM zone_d_activite_ou_d_interet
GROUP BY categorie
HAVING count(*) > 10000
ORDER BY nb DESC;

-- Quelles natures dans la catégorie 'Santé' ?
SELECT nature, count(*) AS nb
FROM zone_d_activite_ou_d_interet
WHERE categorie = 'Santé'
GROUP BY nature
ORDER BY nb DESC;
```

</details>

### Exercice : gendarmeries et casernes

<details>
<summary>Solution</summary>

```sql
SELECT nature, count(*) AS nb
FROM zone_d_activite_ou_d_interet
WHERE categorie = 'Administratif ou militaire'
  AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')
GROUP BY nature;
```

</details>

---

## T0b — SQL : Jointures spatiales

<details>
<summary>Solution — Équipements dans zones industrielles</summary>

```sql
SELECT DISTINCT e.nature, e.nature_detaillee, z.nature AS zone_nature
FROM equipement_de_transport e
JOIN zone_d_activite_ou_d_interet z
  ON ST_Intersects(e.geometrie, z.geometrie)
WHERE z.nature = 'Zone industrielle'
LIMIT 20;
```

</details>

### Exercice : aérodromes et hôpitaux

<details>
<summary>Solution</summary>

```sql
SELECT a.toponyme AS aero, z.toponyme AS hopital,
       ST_Distance(a.geometrie, z.geometrie) AS distance_m
FROM aerodrome a
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(a.geometrie, z.geometrie, 2000)
WHERE z.nature IN ('Hôpital', 'Établissement hospitalier');
```

</details>

---

## T0c — Cypher : premiers pas

<details>
<summary>Solution — Lister l'ontologie</summary>

```cypher
-- Lister les niveaux de l'ontologie
MATCH (n:ClasseOntologie) RETURN n.obj_type, n.name LIMIT 20;

-- Trouver les enfants directs de "Tronçon de route"
MATCH (d)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Tronçon de route'})
RETURN d.obj_type, d.name;

-- Compter les nœuds par label
MATCH (n) RETURN labels(n)[0] AS label, count(*) ORDER BY count DESC;
```

</details>

### Exercice : sous-types de "Construction ponctuelle"

<details>
<summary>Solution</summary>

```cypher
MATCH (d:Detail)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Construction ponctuelle'})
RETURN d.obj_type, d.name;
// Compter :
MATCH (d:Detail)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Construction ponctuelle'})
RETURN count(d) AS nb_sous_types;
```

</details>

---

## T1 — Explorer l'ontologie BDTOPO

<details>
<summary>Solution — Hiérarchie récursive</summary>

```sql
WITH RECURSIVE hierarchy AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
    FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id
)
SELECT depth, obj_type, name FROM hierarchy ORDER BY depth;
```

</details>

---

## T2 — Sélectionner les POIs de votre rôle

<details>
<summary>Solution — Template d'insertion</summary>

```sql
INSERT INTO mission_pois (role, source, cleabs, categorie, nature, nom, geom)
SELECT 'votre_role', 'source_table', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
FROM votre_table
WHERE vos_filtres;
```

Consultez votre page rôle pour les tables et filtres spécifiques :
[Attaque]({% link _docs/roles/attaque.md %}),
[Défense]({% link _docs/roles/defense.md %}),
[Ravitaillement]({% link _docs/roles/ravitaillement.md %}),
[Énergie]({% link _docs/roles/energie.md %}).

</details>

---

## T3 — Ajouter des critères de criticité

<details>
<summary>Solution — Critères par type</summary>

```sql
-- Postes électriques critiques
UPDATE mission_pois SET categorie = 'critique'
WHERE role = 'energie' AND source = 'poste_ht'
  AND CAST(nature AS INTEGER) <= 3;

-- Aérodromes majeurs (déjà filtré à l'insertion)
-- Zones militaires (déjà filtré à l'insertion)

-- Vérification
SELECT role, source, categorie, count(*)
FROM mission_pois
GROUP BY role, source, categorie
ORDER BY role, source;
```

</details>

---

## T4 — Clusteriser les POIs (ST_ClusterDBSCAN)

<details>
<summary>Solution</summary>

```sql
WITH clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid
    FROM mission_pois
)
SELECT cid, COUNT(*) FROM clustered WHERE cid IS NOT NULL GROUP BY cid ORDER BY count DESC;
```

**Variante eps** :

```sql
-- Tester plusieurs seuils
SELECT 1000 AS eps, count(DISTINCT cid) AS nb_clusters
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 1000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 3000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 5000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 5000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL;
```

</details>

---

## T5 — Partager vos POIs

<details>
<summary>Solution — Vérification</summary>

```sql
SELECT role, source, count(*) FROM mission_pois GROUP BY role, source ORDER BY role, count DESC;
```

Chaque rôle doit apparaître avec au moins 1 source. Si un rôle est manquant → l'agent concerné n'a pas encore inséré ses POIs.

</details>

---

## T6 — Questions bonus par rôle

→ Voir [Corrigé Rôles bonus]({% link _docs/corriges/corrige_roles_bonus.md %})

---

## T7 — Cross-rôle

<details>
<summary>Solution — Exemples de requêtes cross-rôle</summary>

**Défense → Énergie** : postes HT à < 1 km d'un hôpital

```sql
SELECT pt.importance, h.toponyme AS hopital,
       ST_Distance(pt.geometrie, h.geometrie) AS dist_m
FROM poste_de_transformation pt
JOIN zone_d_activite_ou_d_interet h
  ON ST_DWithin(pt.geometrie, h.geometrie, 1000)
WHERE CAST(pt.importance AS INTEGER) <= 3
  AND h.nature IN ('Hôpital', 'Établissement hospitalier');
```

**Attaque → Ravitaillement** : ports proches de casernes

```sql
SELECT p.toponyme AS port, z.toponyme AS caserne,
       ST_Distance(p.geometrie, z.geometrie) AS dist_m
FROM equipement_de_transport p
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(p.geometrie, z.geometrie, 5000)
WHERE p.nature = 'Port'
  AND z.nature IN ('Gendarmerie', 'Caserne')
ORDER BY dist_m;
```

**Énergie → Défense** : ponts croisant des lignes THT

```sql
SELECT l.voltage, count(*) AS ponts_fragiles
FROM ligne_electrique l
JOIN construction_surfacique c
  ON ST_Intersects(l.geometrie, c.geometrie)
WHERE l.voltage IN ('400 kV', '225 kV')
  AND c.nature = 'Pont'
GROUP BY l.voltage;
```

**Ravitaillement → Attaque** : zones industrielles proches d'aérodromes

```sql
SELECT z.toponyme AS zone, a.toponyme AS aero,
       ST_Distance(z.geometrie, a.geometrie) AS dist_m
FROM zone_d_activite_ou_d_interet z
JOIN aerodrome a
  ON ST_DWithin(z.geometrie, a.geometrie, 3000)
WHERE z.nature IN ('Zone industrielle', 'Zone d''activités')
  AND a.categorie IN ('Internationale', 'Nationale')
ORDER BY dist_m;
```

</details>
