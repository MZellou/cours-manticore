#!/bin/bash
# Validate one role across all 3 phases on the current DB state
# Usage: ./validate_role_v2.sh <role>
# DB must already be set up (00_setup + 01_explore + 02_migrate)
set -euo pipefail

ROLE="$1"
ROOT="/home/MZellou/Documents/IGN/cours/cours-manticore"
VDIR="$ROOT/validation/$ROLE"
export PGPASSWORD=manticore2026
PSQL="psql -h localhost -U postgres -d bdtopo_manticore -t -A --pset footer=off"
CYPHER="docker exec -i manticore-neo4j cypher-shell -u neo4j -p manticore2026"

mkdir -p "$VDIR"/{phase1,phase2,phase3}

run_sql() {
    local task_id="$1"
    local phase="$2"
    local sql="$3"
    echo "$sql" > "$VDIR/${phase}/${task_id}_input.sql"
    echo "$sql" | $PSQL 2>&1 | head -200 > "$VDIR/${phase}/${task_id}_output.txt"
    local lines
    lines=$(wc -l < "$VDIR/${phase}/${task_id}_output.txt")
    echo "  $task_id: $lines lines"
}

run_cypher() {
    local task_id="$1"
    local phase="$2"
    local query="$3"
    echo "$query" > "$VDIR/${phase}/${task_id}_input.cypher"
    timeout 30 $CYPHER < "$VDIR/${phase}/${task_id}_input.cypher" 2>&1 | head -200 > "$VDIR/${phase}/${task_id}_output.txt" || echo "TIMEOUT" >> "$VDIR/${phase}/${task_id}_output.txt"
    local lines
    lines=$(wc -l < "$VDIR/${phase}/${task_id}_output.txt")
    echo "  $task_id: $lines lines"
}

echo "═══ VALIDATING: $ROLE ═══"

# ─── PHASE 1 ──────────────────────────────────────────────────────
echo ""
echo "PHASE 1 — Reconnaissance (SQL)"

run_sql "T0a_1" "phase1" "SELECT categorie, count(*) AS nb FROM zone_d_activite_ou_d_interet GROUP BY categorie ORDER BY nb DESC;"
run_sql "T0a_2" "phase1" "SELECT categorie, count(*) AS nb FROM zone_d_activite_ou_d_interet GROUP BY categorie HAVING count(*) > 10 ORDER BY nb DESC;"
run_sql "T0a_3" "phase1" "SELECT nature, count(*) AS nb FROM zone_d_activite_ou_d_interet WHERE categorie = 'Santé' GROUP BY nature ORDER BY nb DESC;"
run_sql "T0b_1" "phase1" "SELECT DISTINCT e.nature, e.nature_detaillee, z.nature AS zone_nature FROM equipement_de_transport e JOIN zone_d_activite_ou_d_interet z ON ST_Intersects(e.geometrie, z.geometrie) WHERE z.nature = 'Zone industrielle' LIMIT 20;"
run_sql "T1_1" "phase1" "WITH RECURSIVE hierarchy AS (SELECT id, name, obj_type, parent_id, 0 AS depth FROM bdtopo_ontology WHERE name = 'Tronçon de route' UNION ALL SELECT child.id, child.name, child.obj_type, child.parent_id, h.depth+1 FROM bdtopo_ontology child JOIN hierarchy h ON child.parent_id = h.id) SELECT depth, obj_type, name FROM hierarchy ORDER BY depth LIMIT 20;"
run_sql "T2_1" "phase1" "SELECT source, count(*) AS nb FROM mission_pois WHERE role = '$ROLE' GROUP BY source ORDER BY nb DESC;"
run_sql "T2_2" "phase1" "SELECT count(*) AS total FROM mission_pois WHERE role = '$ROLE';"
run_sql "T3_1" "phase1" "SELECT p.source AS poi_source, count(*) AS nb_within_2km FROM mission_pois p JOIN zone_d_activite_ou_d_interet z ON ST_DWithin(p.geom, z.geometrie, 2000) WHERE p.role = '$ROLE' AND z.nature = 'Zone industrielle' GROUP BY p.source ORDER BY nb_within_2km DESC;"
run_sql "T4_1" "phase1" "WITH clustered AS (SELECT *, ST_ClusterDBSCAN(geom, eps := 500, minpoints := 3) OVER() AS cluster_id FROM mission_pois WHERE role = '$ROLE') SELECT cluster_id, count(*) AS nb FROM clustered WHERE cluster_id IS NOT NULL GROUP BY cluster_id ORDER BY nb DESC LIMIT 10;"
run_sql "T4_2" "phase1" "WITH clustered AS (SELECT *, ST_ClusterDBSCAN(geom, eps := 1000, minpoints := 2) OVER() AS cluster_id FROM mission_pois WHERE role = '$ROLE') SELECT cluster_id, count(*) AS nb, array_agg(source) AS sources FROM clustered WHERE cluster_id IS NOT NULL GROUP BY cluster_id ORDER BY nb DESC LIMIT 10;"
run_sql "T5_1" "phase1" "SELECT r1.source AS source1, r2.source AS source2, count(*) AS paires_proches FROM mission_pois r1 JOIN mission_pois r2 ON r1.role = '$ROLE' AND r2.role <> '$ROLE' AND ST_DWithin(r1.geom, r2.geom, 1000) AND r1.cleabs < r2.cleabs GROUP BY r1.source, r2.source ORDER BY paires_proches DESC LIMIT 15;"
run_sql "T7_1" "phase1" "WITH clustered AS (SELECT role, source, ST_ClusterDBSCAN(geom, 500, 3) OVER() AS cid FROM mission_pois) SELECT cid, count(DISTINCT role) AS nb_roles, array_agg(DISTINCT role) AS roles FROM clustered WHERE cid IS NOT NULL GROUP BY cid HAVING count(DISTINCT role) > 1 ORDER BY nb_roles DESC LIMIT 10;"
run_sql "B1" "phase1" "SELECT nature, count(*) FROM construction_ponctuelle WHERE nature IN ('Tour', 'Antenne', 'Château d''eau', 'Éolienne') GROUP BY nature ORDER BY count DESC;"
run_sql "B2" "phase1" "SELECT count(*) FROM mission_pois p JOIN reservoir r ON ST_DWithin(p.geom, r.geometrie, 3000) WHERE p.role = '$ROLE' AND r.nature = 'Réservoir industriel';"
run_sql "B3" "phase1" "SELECT count(*) FROM mission_pois p JOIN zone_d_activite_ou_d_interet z ON ST_DWithin(p.geom, z.geometrie, 5000) WHERE p.role = '$ROLE' AND z.categorie = 'Enseignement';"
run_sql "B4" "phase1" "SELECT z.nature, count(*) AS nb FROM zone_d_activite_ou_d_interet z JOIN mission_pois p ON ST_DWithin(z.geometrie, p.geom, 2000) WHERE p.role = '$ROLE' AND z.categorie = 'Santé' GROUP BY z.nature ORDER BY nb DESC;"
run_sql "B5" "phase1" "WITH clusters AS (SELECT *, ST_ClusterDBSCAN(geom, 1000, 2) OVER() AS cid FROM mission_pois WHERE role = '$ROLE') SELECT cid, count(*) AS nb, ST_AsText(ST_Centroid(ST_Collect(geom))) AS centre FROM clusters WHERE cid IS NOT NULL GROUP BY cid ORDER BY nb DESC LIMIT 5;"
run_sql "B6" "phase1" "SELECT p1.source, p2.source, ROUND(ST_Distance(p1.geom, p2.geom)::numeric, 0) AS dist_m FROM mission_pois p1 CROSS JOIN mission_pois p2 WHERE p1.role = '$ROLE' AND p2.role = '$ROLE' AND p1.cleabs < p2.cleabs ORDER BY dist_m ASC LIMIT 10;"
run_sql "B7" "phase1" "SELECT source, ROUND(AVG(ST_X(ST_Centroid(geom)))::numeric, 4) AS avg_lon, ROUND(AVG(ST_Y(ST_Centroid(geom)))::numeric, 4) AS avg_lat FROM mission_pois WHERE role = '$ROLE' GROUP BY source ORDER BY source;"

# ─── PHASE 2 ──────────────────────────────────────────────────────
echo ""
echo "PHASE 2 — Cartographie Neo4j (Cypher)"

run_cypher "T0" "phase2" "CALL db.labels();"
run_cypher "T1_1" "phase2" "MATCH (c:ClasseOntologie) RETURN count(c) AS nb_classes;"
run_cypher "T1_2" "phase2" "MATCH (p:POI) RETURN p.role AS role, count(p) AS nb ORDER BY role;"
run_cypher "T1_3" "phase2" "MATCH (c:ClasseOntologie) WHERE c.obj_type = 'Object' RETURN c.name LIMIT 10;"
run_cypher "T2_1" "phase2" "MATCH (c:ClasseOntologie {name: 'Bâtiment'})<-[:EST_SOUS_TYPE_DE*1..6]-(child) RETURN child.name, child.obj_type LIMIT 20;"
# FIX: direction reversed — EST_SOUS_TYPE_DE points child→parent
run_cypher "T2_2" "phase2" "MATCH path = (child:ClasseOntologie)-[:EST_SOUS_TYPE_DE*1..3]->(root:ClasseOntologie {obj_type: 'Database'}) RETURN [n IN nodes(path) | n.name] AS names LIMIT 10;"
run_cypher "T3_1" "phase2" "MATCH (p:POI {role: '$ROLE'}) RETURN p.nom, p.nature, p.source LIMIT 15;"
run_cypher "T3_2" "phase2" "MATCH (p:POI {role: '$ROLE'}) RETURN p.source AS src, count(*) AS nb ORDER BY nb DESC;"
run_cypher "T4_1" "phase2" "MATCH (p:POI {role: '$ROLE'})-[d:DISTANCE]->(q) RETURN p.nom, q.nom, d.meters ORDER BY d.meters LIMIT 10;"
run_cypher "T4_2" "phase2" "MATCH (p:POI {role: '$ROLE'})-[d:DISTANCE]->(q:POI) RETURN count(d) AS nb_relations, avg(d.meters) AS avg_dist, min(d.meters) AS min_dist, max(d.meters) AS max_dist;"
run_cypher "T5_1" "phase2" "MATCH (p:POI {role: '$ROLE'})-[d:DISTANCE]->(q) WHERE d.meters < 1000 RETURN p.nom, q.nom, d.meters ORDER BY d.meters LIMIT 10;"
run_cypher "T6_1" "phase2" "MATCH (p:POI {role: '$ROLE'}) RETURN p.source, count(*) AS nb ORDER BY nb DESC LIMIT 10;"
run_cypher "T7_1" "phase2" "MATCH (a:POI {role: '$ROLE'})-[d:DISTANCE]->(b:POI) WHERE b.role <> '$ROLE' RETURN b.role AS other_role, count(*) AS nb_links ORDER BY nb_links DESC LIMIT 10;"
run_cypher "T8_1" "phase2" "MATCH (a:POI {role: '$ROLE'}), (b:POI {role: '$ROLE'}) WHERE id(a) < id(b) WITH a, b LIMIT 50 MATCH p = shortestPath((a)-[:DISTANCE*1..5]-(b)) RETURN a.nom, b.nom, length(p) AS hops, reduce(t=0, r IN relationships(p) | t+r.meters) AS dist_m ORDER BY dist_m LIMIT 5;"
run_cypher "T9_1" "phase2" "MATCH path = (a:POI {role: '$ROLE'})-[:DISTANCE*1..3]-(b) RETURN [n IN nodes(path) | n.nom] AS etapes, length(path) AS sauts LIMIT 5;"
run_cypher "T9_2" "phase2" "MATCH (a:POI {role: '$ROLE'})-[:DISTANCE]-(b:POI)-[:DISTANCE]-(c:POI)-[:DISTANCE]-(a) WHERE id(a) < id(b) AND id(b) < id(c) RETURN a.nom, b.nom, c.nom LIMIT 10;"
run_cypher "T10_1" "phase2" "MATCH (p:POI {role: '$ROLE'})-[d:DISTANCE]->() RETURN p.source AS src, count(d) AS nb_voisins, avg(d.meters) AS dist_moy ORDER BY nb_voisins DESC;"

# ─── PHASE 3 ──────────────────────────────────────────────────────
echo ""
echo "PHASE 3 — Simulation & Benchmark"

run_sql "T0_1" "phase3" "SELECT count(*) AS total_edges, count(*) FILTER (WHERE cost IS NOT NULL) AS carrossable, count(*) FILTER (WHERE cost IS NULL) AS non_carrossable FROM ways;"
run_sql "T0_2" "phase3" "SELECT count(*) AS vertices FROM ways_vertices_pgr;"
run_sql "T1a_1" "phase3" "WITH comps AS (SELECT node, component FROM pgr_connectedComponents('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL')), main AS (SELECT component FROM comps GROUP BY component ORDER BY count(*) DESC LIMIT 1) SELECT * FROM pgr_dijkstra('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', (SELECT w.source FROM ways w JOIN comps c ON w.source = c.node WHERE c.component = (SELECT component FROM main) ORDER BY random() LIMIT 1), (SELECT w.target FROM ways w JOIN comps c ON w.target = c.node WHERE c.component = (SELECT component FROM main) ORDER BY random() LIMIT 1), directed := false) LIMIT 5;"
run_sql "T1b_1" "phase3" "WITH nearest AS (SELECT p.cleabs, p.nom, (SELECT v.id FROM ways_vertices_pgr v ORDER BY v.geom <-> p.geom LIMIT 1) AS vid FROM mission_pois p WHERE p.role = '$ROLE' LIMIT 2) SELECT a.nom AS start, b.nom AS end, agg.cost FROM nearest a, nearest b, LATERAL (SELECT sum(cost) AS cost FROM pgr_dijkstra('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', a.vid, b.vid, directed := false) WHERE edge != -1) agg WHERE a.cleabs < b.cleabs LIMIT 5;"
run_sql "T2a_1" "phase3" "WITH nearest AS (SELECT p.nom, (SELECT v.id FROM ways_vertices_pgr v ORDER BY v.geom <-> p.geom LIMIT 1) AS vid FROM mission_pois p WHERE p.role = '$ROLE' LIMIT 2) SELECT * FROM pgr_ksp('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', (SELECT vid FROM nearest LIMIT 1), (SELECT vid FROM nearest OFFSET 1 LIMIT 1), 3, directed := false) LIMIT 10;"
run_sql "T2b_1" "phase3" "SELECT count(*) AS total, count(*) FILTER (WHERE nature = 'Chemin') AS chemins, count(*) FILTER (WHERE importance = '1' OR importance = '2' OR importance = '3') AS importance_haute FROM ways;"
run_sql "T2b_2" "phase3" "WITH src AS (SELECT id FROM ways_vertices_pgr WHERE id IN (SELECT source FROM ways WHERE cost IS NOT NULL) ORDER BY id LIMIT 1), tgt AS (SELECT id FROM ways_vertices_pgr WHERE id IN (SELECT source FROM ways WHERE cost IS NOT NULL) ORDER BY id OFFSET 100 LIMIT 1) SELECT * FROM pgr_dijkstra('SELECT id, source, target, CASE WHEN importance IN (''1'',''2'',''3'',''4'') THEN cost ELSE -1 END AS cost, CASE WHEN importance IN (''1'',''2'',''3'',''4'') THEN reverse_cost ELSE -1 END AS reverse_cost FROM ways', (SELECT id FROM src), (SELECT id FROM tgt), directed := true) LIMIT 5;"
run_sql "T3_1" "phase3" "WITH start_v AS (SELECT v.id FROM ways_vertices_pgr v ORDER BY (SELECT geom FROM mission_pois WHERE role = '$ROLE' LIMIT 1) <-> v.geom LIMIT 1) SELECT * FROM pgr_drivingdistance('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', (SELECT id FROM start_v), 3000, directed := false) LIMIT 20;"
run_sql "T4_1" "phase3" "WITH start_v AS (SELECT v.id FROM ways_vertices_pgr v ORDER BY (SELECT geom FROM mission_pois WHERE role = '$ROLE' LIMIT 1) <-> v.geom LIMIT 1), dd AS (SELECT node, agg_cost FROM pgr_drivingdistance('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', (SELECT id FROM start_v), 5000, directed := false)), edges AS (SELECT w.id, w.source, w.target, w.nature FROM ways w WHERE w.source IN (SELECT node FROM dd) AND w.target IN (SELECT node FROM dd)) SELECT nature, count(*) AS nb FROM edges GROUP BY nature ORDER BY nb DESC LIMIT 10;"
run_sql "T5_sql" "phase3" "EXPLAIN ANALYZE SELECT p1.nom, p2.nom, ROUND(ST_Distance(p1.geom, p2.geom)::numeric) AS dist_m FROM mission_pois p1 JOIN mission_pois p2 ON p1.role = '$ROLE' AND p2.role = '$ROLE' AND p1.cleabs < p2.cleabs AND ST_DWithin(p1.geom, p2.geom, 5000) ORDER BY dist_m LIMIT 20;"
run_cypher "T5_cypher" "phase3" "MATCH (a:POI {role: '$ROLE'})-[d:DISTANCE]->(b:POI {role: '$ROLE'}) WHERE d.meters < 5000 RETURN a.nom, b.nom, d.meters ORDER BY d.meters LIMIT 20;"
run_sql "T6_1" "phase3" "WITH nearest AS (SELECT p.nom, p.source, (SELECT v.id FROM ways_vertices_pgr v ORDER BY v.geom <-> p.geom LIMIT 1) AS vid FROM mission_pois p WHERE p.role = '$ROLE'), pairs AS (SELECT a.nom AS from_name, a.source AS from_src, b.nom AS to_name, b.source AS to_src, a.vid AS from_vid, b.vid AS to_vid FROM nearest a, nearest b WHERE a.vid <> b.vid AND a.source < b.source LIMIT 5), routes AS (SELECT p.from_name, p.to_name, (SELECT sum(cost) FROM pgr_dijkstra('SELECT id, source, target, cost, reverse_cost FROM ways WHERE cost IS NOT NULL', p.from_vid, p.to_vid, directed := false) WHERE edge != -1) AS dist_m FROM pairs p) SELECT * FROM routes WHERE dist_m IS NOT NULL ORDER BY dist_m LIMIT 5;"

echo ""
echo "═══ DONE: $ROLE ═══"
echo "Outputs in: $VDIR/"
