# cours-manticore — Agent Guide (Opération Manticore V2)

## Project identity

Teaching repo: DB course (NoSQL graph + spatial), IGN/BDTOPO context.
**Format:** 0.5J theory + 2J hands-on, 40 students / 10 groups × 4 roles.
**Immersive project:** 3 connected phases (Reconnaissance → Cartographie → Simulation).

## Environment

```bash
cp .env.example .env && docker compose up -d   # PostGIS (w/ pgRouting) + Neo4j
uv sync                                          # Python deps (>=3.11)
```

**Makefile shortcuts:**
```bash
make help          # Show all available commands
make setup         # Full student setup: submodule + data + docker + uv
make data-pull     # Pull data from Cloudflare R2
make data-push     # Push data to R2 (instructor only)
make up / make down         # Start/stop containers
make clean / make restart  # Clean volumes or full restart
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
  admin_generate_gold_dumps.py  # Instructor: r2gg for 10 EPCIs
data/
  epci.parquet                    # EPCI geometries
  poi_source/                     # BDTOPO Parquet files (per table)
  ontologie/                      # BDTOPO ontology Parquet files
  gold_dumps/                     # Pre-computed road topology (r2gg output)
mission/                   # Student briefings
  00_briefing.md           # Group assignments + roles
  phase_{1,2,3}_*.md       # Phase briefings
  roles/{attaque,defense,ravitaillement,energie}.md
slides/                    # Marp theory slides
site/                      # Jekyll + just-the-docs (GitHub Pages)
```

## Key concepts

- **4 roles:** Attaque (targets), Défense (protection), Ravitaillement (logistics), Énergie (energy grid)
- **10 EPCIs:** Diverse profiles (ports, borders, mountains, nuclear)
- BDTOPO ontology: 3 levels (`Database → Object → Detail`) linked by `parent_id`
- Neo4j labels: `:ClasseOntologie`, `:POI` with role/source properties
- Main relations: `[:EST_SOUS_TYPE_DE]`, `[:DISTANCE {meters}]`
- Spatial ops: PostGIS (ST_Intersects, ST_DWithin, ST_ClusterDBSCAN) + pgRouting

## Best Practices & Lessons Learned

### Data Extraction
- **Parquet BBOX pushdown:** Reading `geometrie_bbox[0]` from a row gets the FIRST row's bbox, not the row group extent. Use `pf.metadata.row_group(i).column(j).statistics` on `geometrie_bbox.{xmin,xmax,ymin,ymax}` sub-columns.
- **DuckDB > shapely for bulk EPCI filtering:** ~25s for 13 EPCIs vs shapely row-by-row. BBOX pre-extraction is sufficient; exact filtering happens in PostGIS at query time.
- **EPCI key:** Always use `code_siren` (string, 9 chars) as canonical key. Never `nom_officiel` (accents, spaces, fragile).

### Project Structure
- **Admin scripts:** Keep `admin_*.py` separate from student scripts. Produce small per-EPCI artifacts students can download independently.
- **Gold Dumps for road topology:** Pre-computed, avoid live r2gg in TD.
- **Nuclear plants:** Not in BDTOPO — injected as custom POIs at setup.
- **Role queries:** Each role has specific table+filter combos (see `contenu_donnees.md`).
- **Avoid backslashes in f-strings** (compatibility issues with SQL strings).
- **site/**: Jekyll + just-the-docs deployed to GitHub Pages; run `make docs` or build manually.
