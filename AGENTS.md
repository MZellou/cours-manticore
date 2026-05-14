# AGENT ok.md

# cours-manticore — Agent Guide (Opération Manticore V2)

## Project identity

Teaching repo: DB course (NoSQL graph + spatial), IGN/BDTOPO context.
**Format:** 0.5J theory + 2J hands-on, 40 students / 10 groups × 4 roles (× 3 EPCIs bonus = 13 EPCIs total).
**Immersive project:** 3 connected phases (Reconnaissance → Cartographie → Simulation).

## Environment

```bash
cp .env.example .env && docker compose up -d   # PostGIS (w/ pgRouting) + Neo4j
uv sync                                          # Python deps (>=3.11)
python scripts/00_setup.py --epci "<EPCI name>" # canonical entry point: loads ontology + POIs + nuclear plants
```

Optional routing stack (OSRM + Valhalla, not needed for the TD):
`docker compose -f docker-compose.routing.yml up -d`

**Default credentials** (from `.env.example`):
- PostGIS — db `bdtopo_manticore`, user `postgres`, pass `manticore2026`
- Neo4j — user `neo4j`, pass `manticore2026`

**Makefile shortcuts:**
```bash
make help          # Show all available commands
make setup         # Full student setup: submodule + data + docker + uv
make data-pull     # Pull data from Cloudflare R2
make data-push     # Push data to R2 (instructor only)
make up / make down         # Start/stop containers
make clean / make restart  # Clean volumes or full restart
make preview       # Live preview Quarto site (localhost:4200)
make build         # Build Quarto site to _site/
make publish       # Build + push to gh-pages (via GitHub Actions)
```

- PostGIS: `localhost:5432` (includes pgRouting)
- Neo4j: `7474` (browser) + `7687` (bolt) + APOC
- **Data:** Public Cloudflare R2 bucket (`pub-XXXX.r2.dev`) + local `data/epci.parquet` for EPCI geometries.
- **Gold Dumps:** Pre-computed road topology (`data/gold_dumps/`).
- **Nuclear plants:** In BDTOPO as `zone_d_activite_ou_d_interet` WHERE `nature = 'Centrale électrique'`.

## Architecture

```
scripts/
  00_setup.py              # Load EPCI + Ontology + BDTOPO tables
  01_explore_postgis.py    # Phase 1: Role-based POI queries + ST_ClusterDBSCAN
  02_migrate_to_neo4j.py   # Phase 2: Migrate ontology + POIs → Neo4j (APOC)
  03_routing_pgrouting.py  # Phase 2+3: Dijkstra + constrained routing + choke points
  04_benchmark_comparison.py  # Phase 3: SQL vs Cypher benchmark + generate_situation_map()
  admin_extract_epci_data.py  # Instructor: per-EPCI BDTOPO slicing (BBOX pushdown)
  admin_generate_gold_dumps.py  # Instructor: r2gg pipeline (LOAD → R2GG → DUMP) for 13 EPCIs
data/
  epci.parquet                    # EPCI geometries
  poi_source/                     # BDTOPO Parquet files (per table)
  ontologie/                      # BDTOPO ontology Parquet files
  gold_dumps/                     # Pre-computed road topology (r2gg output)
theorie/                   # Theory pages (Quarto)
mission/                   # Student briefings (Quarto)
  briefing.md, phase_{1,2,3}.qmd, checkpoint_{1,2}.qmd, transition_{1_2,2_3}.qmd, debriefing.qmd
roles/                    # Role briefings (Quarto)
corriges/                 # Solutions (Quarto)
reference/                # Setup, scripts, FAQ, glossaire, instructeur (Quarto)
slides/                   # Revealjs slides (generated from theory via {{< include >}})
route-graph-generator/     # IGNF r2gg submodule — used by admin_generate_gold_dumps.py only
```

## Key concepts

- **4 roles:** Attaque (targets), Défense (protection), Ravitaillement (logistics), Énergie (energy grid)
- **13 EPCIs:** Diverse profiles (ports, borders, mountains, nuclear)
- BDTOPO ontology: 3 levels (`Database → Object → Detail`) linked by `parent_id`
- Neo4j labels: `:ClasseOntologie`, `:POI` with role/source properties
- Main relations: `[:EST_SOUS_TYPE_DE]`, `[:DISTANCE {meters}]`
- Spatial ops: PostGIS (ST_Intersects, ST_DWithin, ST_ClusterDBSCAN) + pgRouting

## Best Practices & Lessons Learned

- **Spatial Filtering:** BBOX pushdown (pyarrow) before shapely intersection.
- **Parquet BBOX gotcha:** `geometrie_bbox[0]` on a row gives the FIRST row's bbox, not the row-group extent. Use `pf.metadata.row_group(i).column(j).statistics` on `geometrie_bbox.{xmin,xmax,ymin,ymax}` sub-columns.
- **DuckDB > shapely** for bulk EPCI filtering (~25s for 13 EPCIs vs row-by-row); BBOX pre-extract is enough — exact filtering happens in PostGIS at query time.
- **Canonical EPCI key:** `code_siren` (9-char string). Never `nom_officiel` (accents/spaces are fragile).
- **Performance:** Gold Dumps for road topology, avoid live r2gg in TD.
- **Gold Dumps pipeline:** `admin_generate_gold_dumps.py` does LOAD (parquet → PostGIS) → R2GG (sql2pivot + pivot2pgrouting) → DUMP (pg_dump). r2gg needs `pip install -e route-graph-generator/` + system deps (`libxml2-dev`, `libxslt1-dev`).
- **00_setup.py gold dumps:** Automatically restores `data/gold_dumps/{siren}/ways.sql` if present. Use `--skip-gold-dumps` to skip.
- **BDTOPO SRID:** Parquet geometries are WGS84 (4326), NOT Lambert-93 (2154). Always `ST_SetSRID(geom, 4326)` after loading.
- **r2gg without FDW:** Use `sql/bdtopo_v3.3_local.sql` (no Foreign Data Wrapper) — reads tables directly from same DB. Must `CREATE SCHEMA pgr_{siren}` before pivot2pgrouting.
- **r2gg deps:** Patch `requirements/base.txt` to use `psycopg2-binary` instead of `psycopg2`. `matieres_dangereuses_interdites` is TEXT in parquet, needs CASE cast to BOOLEAN in SQL.
- **Nuclear plants:** Not in BDTOPO — injected as custom POIs at setup.
- **Role queries:** Each role has specific table+filter combos (see `reference/glossaire.qmd`).
- **Avoid backslashes in f-strings** (compatibility issues with SQL strings).
- **Site:** Quarto website deployed to GitHub Pages via `.github/workflows/quarto.yml`. Source files at root (`*.qmd`), built to `_site/`. Theory pages under `theorie/`, mission pages under `mission/`, roles under `roles/`, corrigés under `corriges/`. Slides in `slides/` use `{{< include >}}` to reuse theory content.
- **Quizdown:** Checkpoints (`mission/checkpoint_*.qmd`) include interactive quizzes via `quizdown` Quarto extension.
- **Neo4j DISTANCE O(n²) OOM:** All-pairs DISTANCE (<10km) OOMs on 4000+ POIs. Fix: (a) batch 100 POIs, (b) spatial pre-filter `abs(a.lat-b.lat)<0.1`, (c) `dbms.memory.transaction.total.max=2G`.
- **Neo4j nuke via volume:** `DETACH DELETE` OOMs on millions of rels. Use `docker compose down && docker volume rm <project>_neo4j_data`.
- **cypher-shell inside Docker:** CLI not on host. Use `docker exec -i manticore-neo4j cypher-shell -u neo4j -p manticore2026`.
- **Docker env ≠ restart:** `docker compose restart` ignores env changes. Must `docker compose up -d` to recreate.
- **Neo4j 5.x config:** Use `dbms.memory.transaction.total.max` (old-style). Docker env: `NEO4J_dbms_memory_transaction_total_max`.
- **Validation timeouts:** Heavy Cypher queries timeout on dense graphs (>1M rels). Use explicit timeouts or SKIP markers.
- **Role content balance:** Before adding questions/tasks to roles, count existing items per role. Uneven loads (e.g., 15 vs 6-7) mean adding equally worsens imbalance — adapt additions proportionally.
- **Deeper ≠ harder SQL:** When students have LLM access, "push further" means conceptual/architectural thinking (graph modeling trade-offs, SQL ceiling, bridge to next phase) — not more complex syntax.
- **Vary per-role prompts:** Repeating the same question structure across roles (e.g., "propose an LPG schema") feels redundant even with different contexts. Vary the angle per role.
- **Check git history on refactor cues:** When user says "check last commit," recent merges (e.g., 4→3 roles) reveal architectural intent that overrides assumptions about current structure.
- **Stale indexes after refactor:** Index/reference pages drift after structural changes. Flag as quick post-refactor cleanup.
