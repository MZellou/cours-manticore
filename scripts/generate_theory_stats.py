"""
generate_theory_stats.py - Statistiques BDTOPO pour la page theorie.

Lit data/epci_extracts/<SIREN>/*.parquet (sans DB), produit 4 PNGs
dans site/assets/img/theory/.

Pour ajouter/retirer un EPCI : modifier le dict EPCIS ci-dessous.
Usage : uv run python scripts/generate_theory_stats.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_DIR = Path("data/epci_extracts")
OUT_DIR = Path("pages/assets/img/theory")
ONTO_DIR = Path("data/ontologie")
GOLD_DIR = Path("data/gold_dumps")

EPCIS = {
    "242900314": "Brest",       "200084952": "Le Havre",
    "245900428": "Dunkerque",   "200067205": "Cotentin",
    "200040715": "Grenoble",    "246700488": "Strasbourg",
    "200093201": "Lille",       "200067106": "Pays Basque",
    "200023414": "Rouen",       "243300316": "Bordeaux",
    "244400404": "Nantes",      "200046977": "Lyon",
    "243700754": "Tours",
}

POI_TABLES = {
    "zone_d_activite_ou_d_interet": "Zones d'activité",
    "construction_ponctuelle":      "Constructions ponct.",
    "equipement_de_transport":      "Eq. de transport",
    "reservoir":                    "Réservoirs",
    "pylone":                       "Pylônes",
    "ligne_electrique":             "Lignes électriques",
    "construction_lineaire":        "Constructions lin.",
    "terrain_de_sport":             "Terrains de sport",
}

# Toutes les 20 tables BDTOPO par EPCI (pour la matrice d'inventaire)
ALL_TABLES = [
    "aerodrome", "piste_d_aerodrome",
    "zone_d_activite_ou_d_interet", "equipement_de_transport",
    "construction_ponctuelle", "construction_lineaire", "construction_surfacique",
    "reservoir", "pylone", "ligne_electrique", "poste_de_transformation",
    "canalisation", "non_communication",
    "foret_publique", "parc_ou_reserve", "terrain_de_sport",
    "cours_d_eau", "surface_hydrographique",
    "troncon_de_route", "troncon_de_voie_ferree",
]

ROLE_TABLES = {
    "Attaque":     ["aerodrome", "piste_d_aerodrome", "equipement_de_transport",
                    "zone_d_activite_ou_d_interet", "construction_ponctuelle"],
    "Défense":     ["zone_d_activite_ou_d_interet", "construction_surfacique",
                    "construction_lineaire", "foret_publique", "equipement_de_transport"],
    "Logistique":  ["equipement_de_transport", "reservoir", "troncon_de_voie_ferree",
                    "canalisation", "construction_surfacique", "ligne_electrique",
                    "poste_de_transformation", "pylone", "construction_ponctuelle"],
}


def count_rows(siren: str, table: str) -> int:
    p = DATA_DIR / siren / f"{table}.parquet"
    if not p.exists():
        return 0
    return pq.read_metadata(p).num_rows


def read_col(siren: str, table: str, col: str) -> pd.Series:
    p = DATA_DIR / siren / f"{table}.parquet"
    if not p.exists():
        return pd.Series(dtype=object)
    return pq.read_table(p, columns=[col]).to_pandas()[col]


def chart_poi_counts():
    """Barres groupées : POIs par EPCI et par table."""
    rows = []
    for siren, name in EPCIS.items():
        for table, label in POI_TABLES.items():
            rows.append({"epci": name, "table": label, "count": count_rows(siren, table)})
    df = pd.DataFrame(rows).pivot(index="epci", columns="table", values="count")
    df = df.loc[df.sum(axis=1).sort_values().index]

    fig, ax = plt.subplots(figsize=(10, 7))
    df.plot(kind="barh", stacked=True, ax=ax, colormap="tab20",
            edgecolor="white", linewidth=0.5)
    ax.set_title("POIs par EPCI et par table BDTOPO", fontsize=13, weight="bold")
    ax.set_xlabel("Nombre de POIs")
    ax.set_ylabel("")
    ax.legend(title="Table", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_poi_counts.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_road_network():
    """Barres horizontales : tronçons routiers par EPCI, urbain vs rural."""
    rows = []
    for siren, name in EPCIS.items():
        urbain = read_col(siren, "troncon_de_route", "urbain")
        rows.append({
            "epci": name,
            "urbain": int((urbain == True).sum()),
            "rural":  int((urbain == False).sum()),
        })
    df = pd.DataFrame(rows).set_index("epci").sort_values(by=["urbain", "rural"])
    df_k = df / 1000.0

    fig, ax = plt.subplots(figsize=(10, 6))
    df_k.plot(kind="barh", stacked=True, ax=ax,
              color=["#2c3e50", "#95a5a6"], edgecolor="white")
    ax.set_title("Réseau routier : tronçons urbains vs ruraux", fontsize=13, weight="bold")
    ax.set_xlabel("Nombre de tronçons (×1000)")
    ax.set_ylabel("")
    ax.legend(["Urbain", "Rural"], loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_road_network.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_role_heatmap():
    """Heatmap : moyenne du nombre de lignes par table pour chaque rôle."""
    all_tables = sorted({t for tables in ROLE_TABLES.values() for t in tables})
    means = {t: np.mean([count_rows(s, t) for s in EPCIS]) for t in all_tables}

    grid = np.zeros((len(ROLE_TABLES), len(all_tables)))
    for i, (_, tables) in enumerate(ROLE_TABLES.items()):
        for j, t in enumerate(all_tables):
            grid[i, j] = means[t] if t in tables else 0

    # Normalisation globale (log-ish) pour distinguer les ordres de grandeur
    nonzero_max = grid[grid > 0].max() if (grid > 0).any() else 1
    norm = np.log1p(grid) / np.log1p(nonzero_max)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    im = ax.imshow(norm, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(all_tables)))
    ax.set_xticklabels([t.replace("_", " ") for t in all_tables], rotation=35, ha="right")
    ax.set_yticks(range(len(ROLE_TABLES)))
    ax.set_yticklabels(list(ROLE_TABLES.keys()))
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            if grid[i, j] > 0:
                ax.text(j, i, f"{int(grid[i, j])}", ha="center", va="center",
                        color="black" if norm[i, j] < 0.6 else "white", fontsize=9)
    ax.set_title("Pertinence des tables par rôle (moyenne sur 13 EPCIs)",
                 fontsize=13, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_role_heatmap.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_road_composition():
    """Barres empilées : composition % du réseau routier par nature."""
    bucket_map = {
        "Type autoroutier":    "Autoroutier",
        "Route à 2 chaussées": "Route 2 chaussées",
        "Route à 1 chaussée":  "Route 1 chaussée",
        "Chemin":              "Chemins/sentiers",
        "Sentier":             "Chemins/sentiers",
    }
    bucket_order = ["Autoroutier", "Route 2 chaussées", "Route 1 chaussée",
                    "Chemins/sentiers", "Autre"]

    rows = []
    for siren, name in EPCIS.items():
        nature = read_col(siren, "troncon_de_route", "nature")
        bucketed = nature.map(bucket_map).fillna("Autre")
        counts = bucketed.value_counts(normalize=True) * 100
        row = {"epci": name}
        for b in bucket_order:
            row[b] = float(counts.get(b, 0))
        rows.append(row)
    df = pd.DataFrame(rows).set_index("epci")
    df = df[bucket_order]
    df = df.loc[df["Autoroutier"].sort_values().index]

    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind="barh", stacked=True, ax=ax,
            color=["#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#7f8c8d"],
            edgecolor="white", linewidth=0.5)
    ax.set_title("Composition du réseau routier par EPCI (% par nature)",
                 fontsize=13, weight="bold")
    ax.set_xlabel("% des tronçons")
    ax.set_ylabel("")
    ax.legend(title="Nature", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_road_composition.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_data_inventory():
    """Heatmap : nombre de lignes par table x EPCI, échelle log."""
    grid = np.array([[count_rows(s, t) for t in ALL_TABLES] for s in EPCIS])
    log_grid = np.log10(grid + 1)

    fig, ax = plt.subplots(figsize=(13, 6.5))
    im = ax.imshow(log_grid, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(ALL_TABLES)))
    ax.set_xticklabels([t.replace("_", " ") for t in ALL_TABLES],
                       rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(EPCIS)))
    ax.set_yticklabels(list(EPCIS.values()), fontsize=9)
    for i, siren in enumerate(EPCIS):
        for j, t in enumerate(ALL_TABLES):
            v = grid[i, j]
            if v > 0:
                txt = f"{v//1000}k" if v >= 1000 else str(v)
                ax.text(j, i, txt, ha="center", va="center",
                        color="white" if log_grid[i, j] < log_grid.max() * 0.5 else "black",
                        fontsize=7)
    cbar = fig.colorbar(im, ax=ax, label="log10(count + 1)")
    ax.set_title("Inventaire BDTOPO : nombre de lignes par table et par EPCI",
                 fontsize=13, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_data_inventory.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_road_density():
    """A — Densité routière (tronçons / km²) par EPCI."""
    import geopandas as gpd
    epci = gpd.read_parquet("data/epci.parquet")
    # canonical key = code_siren (string)
    key_col = "code_siren" if "code_siren" in epci.columns else "siren"
    epci = epci.set_index(epci[key_col].astype(str))
    epci["area_km2"] = epci.geometry.to_crs(2154).area / 1e6

    rows = []
    for siren, name in EPCIS.items():
        n_roads = count_rows(siren, "troncon_de_route")
        area = float(epci.loc[siren, "area_km2"]) if siren in epci.index else np.nan
        rows.append({"epci": name, "tronc_per_km2": n_roads / area if area else 0,
                     "area_km2": area})
    df = pd.DataFrame(rows).set_index("epci").sort_values("tronc_per_km2")

    fig, ax = plt.subplots(figsize=(10, 6))
    df["tronc_per_km2"].plot(kind="barh", ax=ax, color="#34495e", edgecolor="white")
    ax.set_title("Densité du réseau routier — tronçons par km²",
                 fontsize=13, weight="bold")
    ax.set_xlabel("tronçons / km²")
    ax.set_ylabel("")
    for i, v in enumerate(df["tronc_per_km2"]):
        ax.text(v, i, f"  {v:.0f}", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_road_density.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_choke_points():
    """B — Choke-points candidats (ponts + tunnels + barrages) par EPCI."""
    rows = []
    for siren, name in EPCIS.items():
        surf = read_col(siren, "construction_surfacique", "nature")
        line = read_col(siren, "construction_lineaire", "nature")
        ponts_s   = int((surf == "Pont").sum())
        barrages  = int((surf == "Barrage").sum())
        ecluses   = int((surf == "Écluse").sum())
        tunnels   = int(line.isin(["Tunnel", "Tranchée couverte"]).sum())
        ponts_l   = int((line == "Pont").sum())
        rows.append({"epci": name, "Ponts (surf)": ponts_s, "Ponts (linéaires)": ponts_l,
                     "Tunnels": tunnels, "Barrages": barrages, "Écluses": ecluses})
    df = pd.DataFrame(rows).set_index("epci")
    df = df.loc[df.sum(axis=1).sort_values().index]

    fig, ax = plt.subplots(figsize=(10, 7))
    df.plot(kind="barh", stacked=True, ax=ax,
            color=["#2980b9", "#3498db", "#8e44ad", "#c0392b", "#16a085"],
            edgecolor="white", linewidth=0.5)
    ax.set_title("Points singuliers du réseau (candidats choke-points Phase 3)",
                 fontsize=13, weight="bold")
    ax.set_xlabel("Nombre d'ouvrages")
    ax.set_ylabel("")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_choke_points.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_road_importance():
    """C — Pyramide d'importance routière (% par EPCI)."""
    buckets = [("1-2 (national)", {1, 2}), ("3", {3}), ("4", {4}), ("5-6 (local)", {5, 6})]
    rows = []
    for siren, name in EPCIS.items():
        imp = read_col(siren, "troncon_de_route", "importance")
        try:
            imp_int = pd.to_numeric(imp.astype(str).str.replace("'", ""), errors="coerce")
        except Exception:
            imp_int = pd.Series(dtype=float)
        total = imp_int.notna().sum() or 1
        row = {"epci": name}
        for label, vals in buckets:
            row[label] = 100.0 * imp_int.isin(vals).sum() / total
        rows.append(row)
    df = pd.DataFrame(rows).set_index("epci")
    df = df.loc[df["1-2 (national)"].sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind="barh", stacked=True, ax=ax,
            color=["#c0392b", "#e67e22", "#f1c40f", "#bdc3c7"],
            edgecolor="white", linewidth=0.5)
    ax.set_title("Pyramide d'importance routière (% des tronçons)",
                 fontsize=13, weight="bold")
    ax.set_xlabel("% des tronçons")
    ax.set_ylabel("")
    ax.legend(title="Importance", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_road_importance.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_electrical_resilience():
    """D — Résilience électrique : pylônes, postes HT, lignes 400/225 kV."""
    rows = []
    for siren, name in EPCIS.items():
        pyl   = count_rows(siren, "pylone")
        ptr   = count_rows(siren, "poste_de_transformation")
        volt  = read_col(siren, "ligne_electrique", "voltage")
        thtxx = int(volt.isin(["400 kV", "225 kV"]).sum())
        rows.append({"epci": name, "Pylônes": pyl, "Postes HT": ptr,
                     "Lignes 225/400 kV": thtxx})
    df = pd.DataFrame(rows).set_index("epci")
    df_norm = df.div(df.max()).fillna(0)  # normalise pour comparabilité visuelle
    df_norm = df_norm.loc[df["Pylônes"].sort_values().index]

    fig, ax = plt.subplots(figsize=(10, 6))
    df_norm.plot(kind="barh", ax=ax,
                 color=["#16a085", "#2980b9", "#d35400"],
                 edgecolor="white", width=0.8)
    ax.set_title("Réseau électrique par EPCI (valeurs normalisées max=1)",
                 fontsize=13, weight="bold")
    ax.set_xlabel("Ratio (1 = max sur les 13 EPCIs)")
    ax.set_ylabel("")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    # Annoter les valeurs brutes
    for i, epci in enumerate(df_norm.index):
        raw = df.loc[epci]
        ax.annotate(f"  P:{raw['Pylônes']} | HT:{raw['Postes HT']} | THT:{raw['Lignes 225/400 kV']}",
                    xy=(1.02, i), xycoords=("axes fraction", "data"),
                    fontsize=7, color="#555", va="center")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_electrical_resilience.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_ontology_treemap():
    """E — Profondeur de l'ontologie BDTOPO (3 niveaux Database→Object→Detail)."""
    try:
        db   = pq.read_table(ONTO_DIR / "bdtopo_database.parquet").to_pandas()
        obj  = pq.read_table(ONTO_DIR / "bdtopo_objects.parquet").to_pandas()
        det  = pq.read_table(ONTO_DIR / "bdtopo_details.parquet").to_pandas()
    except FileNotFoundError as e:
        print(f"  [skip] ontology files missing: {e}")
        return

    # Details liés aux Objects via parent_obj_name ; Objects liés aux Database via parent_db_name
    det_per_obj = det.groupby("parent_obj_name").size().rename("n_details")
    obj_aug = obj.assign(n_details=obj["name"].map(det_per_obj).fillna(0))
    agg = obj_aug.groupby("parent_db_name").agg(
        n_objects=("name", "count"),
        n_details=("n_details", "sum"),
    ).sort_values("n_details", ascending=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    y = np.arange(len(agg))
    ax.barh(y, agg["n_details"], color="#34495e", label="Details (feuilles)")
    ax.barh(y, agg["n_objects"], color="#e67e22", alpha=0.85, label="Objects")
    ax.set_yticks(y)
    ax.set_yticklabels(agg.index, fontsize=9)
    ax.set_xlabel("Nombre de classes")
    ax.set_title(f"Ontologie BDTOPO — Objects ({len(obj)}) & Details ({len(det)}) par Database",
                 fontsize=13, weight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_ontology.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def _parse_ways_copy(sql_path: Path, cost_idx: int = 47, source_idx: int = 5, target_idx: int = 6):
    """Parse les colonnes utiles depuis le COPY block d'un gold dump pgRouting."""
    costs, sources, targets = [], [], []
    in_copy = False
    with open(sql_path, "r", encoding="utf-8") as f:
        for line in f:
            if not in_copy:
                if line.startswith("COPY ") and ".ways " in line and "FROM stdin" in line:
                    in_copy = True
                continue
            if line.startswith("\\."):
                break
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(cost_idx, source_idx, target_idx):
                continue
            try:
                c = float(parts[cost_idx])
                if c > 0 and c < 1e6:
                    costs.append(c)
                sources.append(int(parts[source_idx]))
                targets.append(int(parts[target_idx]))
            except (ValueError, IndexError):
                continue
    return np.array(costs), np.array(sources), np.array(targets)


def chart_cost_histogram():
    """F — Histogramme cost (s_car) sur 1 EPCI moyen (Brest)."""
    dump = GOLD_DIR / "242900314" / "ways.sql"
    if not dump.exists():
        print(f"  [skip] {dump} missing")
        return
    costs, _, _ = _parse_ways_copy(dump)
    if costs.size == 0:
        print("  [skip] no costs parsed")
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(costs, bins=80, color="#2980b9", edgecolor="white")
    ax.set_xlabel("cost_s_car (secondes par traversée)")
    ax.set_ylabel("Nombre d'arêtes")
    ax.set_yscale("log")
    ax.set_title(f"Distribution des coûts pgRouting (Brest — {costs.size:,} arêtes)".replace(",", " "),
                 fontsize=13, weight="bold")
    ax.axvline(np.median(costs), color="#c0392b", linestyle="--",
               label=f"médiane = {np.median(costs):.1f}s")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_cost_histogram.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def chart_node_degree():
    """G — Distribution du degré des nœuds (log-log) sur 1 EPCI."""
    dump = GOLD_DIR / "242900314" / "ways.sql"
    if not dump.exists():
        print(f"  [skip] {dump} missing")
        return
    _, src, tgt = _parse_ways_copy(dump)
    if src.size == 0:
        return
    endpoints = np.concatenate([src, tgt])
    _, counts = np.unique(endpoints, return_counts=True)
    deg_values, deg_freq = np.unique(counts, return_counts=True)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.scatter(deg_values, deg_freq, color="#16a085", s=30)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Degré du nœud (nombre d'arêtes incidentes)")
    ax.set_ylabel("Nombre de nœuds (log)")
    ax.set_title(f"Distribution du degré — Brest ({counts.size:,} nœuds, deg. moyen = {counts.mean():.2f})".replace(",", " "),
                 fontsize=13, weight="bold")
    ax.grid(which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "chart_node_degree.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def emit_markdown_tables():
    """Génère les tableaux markdown POI + réseau routier (à coller dans contenu_donnees.md)."""
    out = Path("scripts/_generated_tables.md")
    poi_tables = ["aerodrome", "zone_d_activite_ou_d_interet", "equipement_de_transport",
                  "construction_ponctuelle", "construction_surfacique", "reservoir",
                  "ligne_electrique", "poste_de_transformation", "troncon_de_voie_ferree"]
    lines = ["# Tableaux générés (à recopier dans contenu_donnees.md)\n"]
    lines.append("\n## Matrice POI par EPCI\n")
    lines.append("| EPCI | aérod. | zone_act. | eq_transp | constr_ponct. | constr_surf. | réservoir | ligne_élec. | poste_transf. | voie_ferrée |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for siren, name in EPCIS.items():
        cells = [f"{count_rows(siren, t):,}".replace(",", " ") for t in poi_tables]
        lines.append(f"| **{name}** | " + " | ".join(cells) + " |")
    lines.append("\n## Réseau routier par EPCI\n")
    lines.append("| EPCI | Total | Autoroute | Route 2ch | Route 1ch | Bretelle | Chemin | Sentier | Imp≤3 | Restr.poids | Restr.hauteur | Urbain |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for siren, name in EPCIS.items():
        p = DATA_DIR / siren / "troncon_de_route.parquet"
        if not p.exists():
            continue
        df = pq.read_table(p, columns=["nature", "importance", "restriction_de_poids_total",
                                       "restriction_de_hauteur", "urbain"]).to_pandas()
        nat = df["nature"].value_counts()
        try:
            imp_le3 = (df["importance"].astype(str).str.replace("'", "").astype(int) <= 3).sum()
        except Exception:
            imp_le3 = 0
        cells = [
            len(df), nat.get("Type autoroutier", 0), nat.get("Route à 2 chaussées", 0),
            nat.get("Route à 1 chaussée", 0), nat.get("Bretelle", 0),
            nat.get("Chemin", 0), nat.get("Sentier", 0), imp_le3,
            df["restriction_de_poids_total"].notna().sum(),
            df["restriction_de_hauteur"].notna().sum(),
            (df["urbain"] == True).sum(),
        ]
        lines.append(f"| **{name}** | " + " | ".join(f"{c:,}".replace(",", " ") for c in cells) + " |")
    out.write_text("\n".join(lines))


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating charts...")
    chart_poi_counts();             print("  [01/12] chart_poi_counts.png")
    chart_road_network();           print("  [02/12] chart_road_network.png")
    chart_role_heatmap();           print("  [03/12] chart_role_heatmap.png")
    chart_road_composition();       print("  [04/12] chart_road_composition.png")
    chart_data_inventory();         print("  [05/12] chart_data_inventory.png")
    chart_road_density();           print("  [06/12] chart_road_density.png")
    chart_choke_points();           print("  [07/12] chart_choke_points.png")
    chart_road_importance();        print("  [08/12] chart_road_importance.png")
    chart_electrical_resilience();  print("  [09/12] chart_electrical_resilience.png")
    chart_ontology_treemap();       print("  [10/12] chart_ontology.png")
    chart_cost_histogram();         print("  [11/12] chart_cost_histogram.png")
    chart_node_degree();            print("  [12/12] chart_node_degree.png")
    emit_markdown_tables();    print("  Markdown tables written to scripts/_generated_tables.md")
    print(f"Done. Output: {OUT_DIR}/")
