#!/bin/bash
set -euo pipefail

VDIR="/home/MZellou/Documents/IGN/cours/cours-manticore/validation/phase1"
WDIR="/home/MZellou/Documents/IGN/cours/cours-manticore"
export PGPASSWORD=manticore2026
PSQL="psql -h localhost -U postgres -d bdtopo_manticore"

cd "$WDIR"

run_sql() {
    local task_id="$1"
    local sql="$2"
    echo "$sql" > "$VDIR/${task_id}_input.sql"
    echo "$sql" | $PSQL 2>&1 | head -500 > "$VDIR/${task_id}_output.txt"
    local lines=$(grep -c . "$VDIR/${task_id}_output.txt" 2>/dev/null || echo 0)
    echo "  $task_id: $lines lines"
}

run_duckdb() {
    local task_id="$1"
    local sql="$2"
    echo "$sql" > "$VDIR/${task_id}_input.sql"
    echo "$sql" | duckdb -markdown 2>&1 | head -500 > "$VDIR/${task_id}_output.txt"
    local lines=$(grep -c . "$VDIR/${task_id}_output.txt" 2>/dev/null || echo 0)
    echo "  $task_id: $lines lines"
}

run_cypher() {
    local task_id="$1"
    local cypher="$2"
    echo "$cypher" > "$VDIR/${task_id}_input.cypher"
    # Write a temp Python script to avoid quoting issues
    cat > /tmp/cypher_run.py << PYEOF
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'manticore2026'))
s = d.session()
try:
    r = s.run('''${cypher}''')
    for row in r:
        print(dict(row))
except Exception as e:
    print(f'ERROR: {e}')
PYEOF
    uv run python /tmp/cypher_run.py > "$VDIR/${task_id}_output.txt" 2>&1 || true
    local lines=$(grep -c . "$VDIR/${task_id}_output.txt" 2>/dev/null || echo 0)
    echo "  $task_id: $lines lines"
}

echo "=== T0a: DuckDB exploration ==="

run_duckdb T0a_1 "DESCRIBE SELECT * FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet');"

run_duckdb T0a_2 "SELECT categorie, count(*) AS nb FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') GROUP BY categorie ORDER BY nb DESC;"

run_duckdb T0a_3 "SELECT nature, nature_detaillee, count(*) AS cnt FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') WHERE categorie = 'Santé' GROUP BY ALL ORDER BY cnt DESC;"

run_duckdb T0a_4 "SELECT nature, count(*) AS nb FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') WHERE categorie = 'Administratif ou militaire' AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos') GROUP BY nature;"

run_duckdb T0a_5 "SELECT d.nature, d.cnt, o.short_def FROM (SELECT nature, count(*) as cnt FROM read_parquet('data/poi_source/zone_d_activite_ou_d_interet.parquet') WHERE categorie = 'Santé' GROUP BY nature) d LEFT JOIN (SELECT name as obj_name, substring(definition, 1, 120) as short_def FROM read_parquet('data/ontologie/bdtopo_objects.parquet') WHERE parent_db_name = 'zone_d_activite_ou_d_interet') o ON d.nature = o.obj_name ORDER BY d.cnt DESC;"

echo ""
echo "=== T0b: Spatial joins ==="

run_sql T0b_1 "SELECT DISTINCT e.nature, e.nature_detaillee, z.nature AS zone_nature
FROM equipement_de_transport e
JOIN zone_d_activite_ou_d_interet z
  ON ST_Intersects(e.geometrie, z.geometrie)
WHERE z.nature = 'Zone industrielle'
LIMIT 20;"

run_sql T0b_2 "SELECT a.toponyme AS aero, z.toponyme AS hopital,
       ST_Distance(a.geometrie, z.geometrie) AS distance_m
FROM aerodrome a
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(a.geometrie, z.geometrie, 2000)
WHERE z.nature IN ('Hôpital', 'Établissement hospitalier');"

echo ""
echo "=== T0c: Cypher first steps ==="

run_cypher T0c_1 "MATCH (n:ClasseOntologie) RETURN n.obj_type, n.name LIMIT 20"

run_cypher T0c_2 "MATCH (d)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Tronçon de route'}) RETURN d.obj_type, d.name"

run_cypher T0c_3 "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt ORDER BY cnt DESC"

run_cypher T0c_4a "MATCH (d:Detail)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Construction ponctuelle'}) RETURN d.obj_type, d.name"

run_cypher T0c_4b "MATCH (d:Detail)-[:EST_SOUS_TYPE_DE]->(o:Object {name: 'Construction ponctuelle'}) RETURN count(d) AS nb_sous_types"

echo ""
echo "=== T1: Ontology WITH RECURSIVE ==="

run_sql T1 "WITH RECURSIVE hierarchy AS (
    SELECT id, name, obj_type, parent_id, 0 AS depth
    FROM bdtopo_ontology WHERE name = 'Tronçon de route'
    UNION ALL
    SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth + 1
    FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id
)
SELECT depth, obj_type, name FROM hierarchy ORDER BY depth;"

echo ""
echo "=== T2: Select POIs for Attaque role (10 sources) ==="

cat > "$VDIR/T2_input.sql" << 'SQLEOF'
SELECT source, count(*) AS nb FROM (
  SELECT 'aerodrome' AS source, cleabs, categorie, nature, toponyme AS nom, ST_Force2D(geometrie) AS geom
  FROM aerodrome WHERE categorie IN ('Internationale', 'Nationale')
  UNION ALL
  SELECT 'port', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature = 'Port' AND nature_detaillee = 'Port de commerce'
  UNION ALL
  SELECT 'zone_militaire', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE categorie = 'Administratif ou militaire' AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')
  UNION ALL
  SELECT 'tour_controle', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature = 'Tour de contrôle aérien'
  UNION ALL
  SELECT 'fragilite', cleabs, nature, nature_detaillee, NULL, ST_Force2D(geometrie)
  FROM construction_lineaire WHERE nature IN ('Pont', 'Tunnel')
  UNION ALL
  SELECT 'cible_symbolique', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE nature IN ('Préfecture', 'Police', 'Etablissement pénitentiaire', 'Administration centrale')
  UNION ALL
  SELECT 'infra_critique', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM zone_d_activite_ou_d_interet WHERE nature IN ('Station d''épuration', 'Usine de production d''eau potable')
  UNION ALL
  SELECT 'noeud_transport', cleabs, nature, nature_detaillee, toponyme, ST_Force2D(geometrie)
  FROM equipement_de_transport WHERE nature IN ('Gare voyageurs uniquement', 'Aire de repos ou de service', 'Péage')
  UNION ALL
  SELECT 'communication', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM construction_ponctuelle WHERE nature = 'Antenne'
  UNION ALL
  SELECT 'retenue_eau', cleabs, categorie, nature, toponyme, ST_Force2D(geometrie)
  FROM surface_hydrographique WHERE nature IN ('Retenue', 'Retenue-barrage', 'Lac')
) AS poi GROUP BY source ORDER BY nb DESC;
SQLEOF

$PSQL -f "$VDIR/T2_input.sql" 2>&1 | head -500 > "$VDIR/T2_output.txt"
echo "  T2: $(grep -c . $VDIR/T2_output.txt) lines"

echo ""
echo "=== T3: Criticality criteria ==="

run_sql T3 "SELECT role, source, categorie, count(*)
FROM mission_pois
WHERE role = 'attaque'
GROUP BY role, source, categorie
ORDER BY role, source, categorie;"

echo ""
echo "=== T4: DBSCAN clustering ==="

run_sql T4_1 "WITH clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid
    FROM mission_pois
)
SELECT cid, COUNT(*) AS nb FROM clustered WHERE cid IS NOT NULL GROUP BY cid ORDER BY nb DESC;"

run_sql T4_2 "SELECT 1000 AS eps, count(DISTINCT cid) AS nb_clusters
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 1000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 2000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 2000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 3000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL
UNION ALL
SELECT 5000, count(DISTINCT cid)
FROM (SELECT *, ST_ClusterDBSCAN(geom, eps := 5000, minpoints := 2) OVER () AS cid FROM mission_pois) t
WHERE cid IS NOT NULL;"

echo ""
echo "=== T7: Cross-role queries ==="

run_sql T7_1 "SELECT pt.importance, h.toponyme AS hopital,
       ST_Distance(pt.geometrie, h.geometrie) AS dist_m
FROM poste_de_transformation pt
JOIN zone_d_activite_ou_d_interet h
  ON ST_DWithin(pt.geometrie, h.geometrie, 1000)
WHERE CAST(pt.importance AS INTEGER) <= 3
  AND h.nature IN ('Hôpital', 'Établissement hospitalier');"

run_sql T7_2 "SELECT p.toponyme AS port, z.toponyme AS caserne,
       ST_Distance(p.geometrie, z.geometrie) AS dist_m
FROM equipement_de_transport p
JOIN zone_d_activite_ou_d_interet z
  ON ST_DWithin(p.geometrie, z.geometrie, 5000)
WHERE p.nature = 'Port'
  AND z.nature IN ('Gendarmerie', 'Caserne')
ORDER BY dist_m;"

run_sql T7_3 "SELECT l.voltage, count(*) AS ponts_fragiles
FROM ligne_electrique l
JOIN construction_surfacique c
  ON ST_Intersects(l.geometrie, c.geometrie)
WHERE l.voltage IN ('400 kV', '225 kV')
  AND c.nature = 'Pont'
GROUP BY l.voltage;"

run_sql T7_4 "SELECT z.toponyme AS zone, a.toponyme AS aero,
       ST_Distance(z.geometrie, a.geometrie) AS dist_m
FROM zone_d_activite_ou_d_interet z
JOIN aerodrome a
  ON ST_DWithin(z.geometrie, a.geometrie, 3000)
WHERE z.nature IN ('Zone industrielle', 'Zone d''activités')
  AND a.categorie IN ('Internationale', 'Nationale')
ORDER BY dist_m;"

echo ""
echo "=== Bonus B1-B7 (Attaque) ==="

run_sql B1_1 "SELECT a.toponyme AS aero, e.toponyme AS port,
       ST_Distance(a.geometrie, e.geometrie) AS dist_m
FROM aerodrome a
JOIN equipement_de_transport e
  ON ST_DWithin(a.geometrie, e.geometrie, 5000)
WHERE a.categorie IN ('Internationale', 'Nationale')
  AND e.nature = 'Port';"

run_sql B1_2 "SELECT '5km' AS rayon, count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 5000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port'
UNION ALL
SELECT '10km', count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 10000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port'
UNION ALL
SELECT '20km', count(*) FROM aerodrome a
JOIN equipement_de_transport e ON ST_DWithin(a.geometrie, e.geometrie, 20000)
WHERE a.categorie IN ('Internationale', 'Nationale') AND e.nature = 'Port';"

run_sql B2 "WITH forces AS (
    SELECT ST_Force2D(geometrie) AS geom, nature, toponyme
    FROM zone_d_activite_ou_d_interet
    WHERE categorie = 'Administratif ou militaire'
      AND nature IN ('Gendarmerie', 'Caserne', 'Camp militaire non clos')
),
clustered AS (
    SELECT *, ST_ClusterDBSCAN(geom, eps := 3000, minpoints := 2) OVER () AS cid
    FROM forces
)
SELECT cid, count(*) AS nb_forces, string_agg(toponyme, ', ') AS sites
FROM clustered WHERE cid IS NOT NULL
GROUP BY cid ORDER BY nb_forces DESC;"

run_sql B3 "SELECT a.toponyme, a.categorie,
       (SELECT count(*) FROM equipement_de_transport e
        WHERE e.nature = 'Tour de contrôle aérien'
          AND ST_DWithin(e.geometrie, a.geometrie, 1000)) AS tours_proches
FROM aerodrome a
WHERE a.categorie IN ('Internationale', 'Nationale');"

run_sql B4 "SELECT p.nom AS cible, p.nature,
       avg(r.vitesse_moyenne_vl) AS vitesse_moy_kmh
FROM mission_pois p
JOIN troncon_de_route r ON ST_DWithin(p.geom, r.geometrie, 2000)
WHERE p.role = 'attaque'
GROUP BY p.nom, p.nature
ORDER BY vitesse_moy_kmh;"

run_sql B5 "SELECT
    c.nature,
    c.toponyme AS nom_ouvrage,
    r.nature AS type_route,
    r.importance
FROM construction_lineaire c
JOIN troncon_de_route r
    ON ST_Intersects(c.geometrie, r.geometrie)
WHERE c.nature IN ('Pont', 'Tunnel')
  AND CAST(r.importance AS INTEGER) <= 2
ORDER BY c.nature, r.importance;"

run_sql B6 "SELECT
    ST_SnapToGrid(geom, 5000) AS carreau,
    count(*) AS nb_antennes
FROM mission_pois
WHERE role = 'attaque' AND source = 'communication'
GROUP BY ST_SnapToGrid(geom, 5000)
ORDER BY nb_antennes;"

run_sql B7 "SELECT
    p.nom AS cible,
    p.nature,
    s.nature AS type_retenue,
    round(ST_Distance(p.geom, s.geom)::numeric, 0) AS distance_m
FROM mission_pois p
JOIN surface_hydrographique s
    ON ST_DWithin(p.geom, s.geom, 500)
WHERE p.role = 'attaque'
  AND s.nature IN ('Retenue', 'Retenue-barrage', 'Lac')
ORDER BY distance_m;"

echo ""
echo "=== ALL DONE ==="
