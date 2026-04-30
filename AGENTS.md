# AGENT ok.md

# cours-manticore — Agent Guide (Opération Manticore V2)

## Project identity

Teaching repo: DB course (NoSQL graph + spatial), IGN/BDTOPO context.
**Format:** 0.5J theory + 2J hands-on, 40 students / 10 groups × 4 roles.
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
- **Custom POIs:** Nuclear plants injected at setup (`mission_custom_pois` table).

## Architecture

```
scripts/
  00_setup.py              # Load EPCI + Ontology + inject nuclear plants
  01_explore_postgis.py    # Phase 1: Role-based POI queries + ST_ClusterDBSCAN
  02_migrate_to_neo4j.py   # Phase 2: Migrate ontology + POIs → Neo4j (APOC)
  03_routing_pgrouting.py  # Phase 2+3: Dijkstra + constrained routing + choke points
  04_benchmark_comparison.py  # Phase 3: SQL vs Cypher benchmark + generate_situation_map()
  admin_extract_epci_data.py  # Instructor: per-EPCI BDTOPO slicing (BBOX pushdown)
  admin_generate_gold_dumps.py  # Instructor: r2gg for 10 EPCIs
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
- **10 EPCIs:** Diverse profiles (ports, borders, mountains, nuclear)
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
- **Nuclear plants:** Not in BDTOPO — injected as custom POIs at setup.
- **Role queries:** Each role has specific table+filter combos (see `reference/glossaire.qmd`).
- **Avoid backslashes in f-strings** (compatibility issues with SQL strings).
- **Site:** Quarto website deployed to GitHub Pages via `.github/workflows/quarto.yml`. Source files at root (`*.qmd`), built to `_site/`. Theory pages under `theorie/`, mission pages under `mission/`, roles under `roles/`, corrigés under `corriges/`. Slides in `slides/` use `{{< include >}}` to reuse theory content.
- **Quizdown:** Checkpoints (`mission/checkpoint_*.qmd`) include interactive quizzes via `quizdown` Quarto extension.
