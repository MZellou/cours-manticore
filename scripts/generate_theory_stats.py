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
OUT_DIR = Path("site/assets/img/theory")

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
    "Attaque":        ["aerodrome", "piste_d_aerodrome", "equipement_de_transport",
                       "zone_d_activite_ou_d_interet", "construction_ponctuelle"],
    "Défense":        ["zone_d_activite_ou_d_interet", "construction_surfacique",
                       "construction_lineaire", "foret_publique", "equipement_de_transport"],
    "Ravitaillement": ["equipement_de_transport", "reservoir", "troncon_de_voie_ferree",
                       "canalisation", "construction_surfacique"],
    "Énergie":        ["ligne_electrique", "poste_de_transformation", "pylone",
                       "construction_ponctuelle", "construction_surfacique",
                       "reservoir", "canalisation"],
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
    chart_poi_counts();        print("  [1/5] chart_poi_counts.png")
    chart_road_network();      print("  [2/5] chart_road_network.png")
    chart_role_heatmap();      print("  [3/5] chart_role_heatmap.png")
    chart_road_composition();  print("  [4/5] chart_road_composition.png")
    chart_data_inventory();    print("  [5/5] chart_data_inventory.png")
    emit_markdown_tables();    print("  Markdown tables written to scripts/_generated_tables.md")
    print(f"Done. Output: {OUT_DIR}/")
