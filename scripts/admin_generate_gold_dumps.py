"""
admin_generate_gold_dumps.py — Génération des graphes de routage (Instructeur)
=============================================================================
Ce script automatise la génération des topologies pgRouting, OSRM et Valhalla
pour les 10 EPCIs du TD en utilisant Route Graph Generator (r2gg).

Usage :
    python scripts/admin_generate_gold_dumps.py --all
    python scripts/admin_generate_gold_dumps.py --epci "Brest Métropole"
"""

import argparse
import os
import json
import shutil
import subprocess
import sys
import pandas as pd
from pathlib import Path

# =============================================================================
# CONFIG
# =============================================================================

EPCI_PARQUET = "data/epci.parquet"
OUTPUT_DIR = "data/gold_dumps"
R2GG_DIR = "route-graph-generator"

SELECTED_EPCIS = [
    "Brest Métropole",
    "Le Havre Seine Métropole",
    "CU de Dunkerque",
    "CA du Cotentin",
    "Grenoble-Alpes-Métropole",
    "Eurométropole de Strasbourg",
    "Métropole Européenne de Lille",
    "CA du Pays Basque",
    "Métropole Rouen Normandie",
    "Bordeaux Métropole",
]

def generate_r2gg_config(epci_name, siren, bbox, output_path):
    """Génère un fichier de configuration JSON pour r2gg."""
    config = {
        "generation": {
            "general": {
                "id": f"manticore_{siren}",
                "overwrite": True,
                "operation": "creation"
            },
            "bases": [
                {
                    "id": "base_pivot",
                    "type": "bdd",
                    "configFile": "config/db_pivot.json",
                    "schema": "public"
                },
                {
                    "id": "base_sortie",
                    "type": "bdd",
                    "configFile": "config/db_output.json",
                    "schema": f"pgr_{siren}"
                }
            ],
            "resource": {
                "id": f"pgr_{siren}",
                "type": "pgr",
                "sources": [
                    {
                        "id": "bdtopo",
                        "type": "pgr",
                        "projection": "EPSG:4326",
                        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                        "mapping": {
                            "source": {"baseId": "base_pivot"},
                            "conversion": {"file": "sql/bdtopo_v3.3.sql"}
                        }
                    }
                ]
            }
        }
    }
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Générer pour tous les EPCIs")
    parser.add_argument("--epci", help="Nom d'un EPCI spécifique")
    args = parser.parse_args()

    targets = SELECTED_EPCIS if args.all else ([args.epci] if args.epci else [])
    if not targets:
        parser.error("--all ou --epci requis")
        return

    print("[ADMIN] Lancement de la génération des Gold Dumps...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df_epci = pd.read_parquet(EPCI_PARQUET)

    for name in targets:
        print(f"\n--- Traitement de : {name} ---")
        res = df_epci[df_epci["nom_officiel"] == name]
        if res.empty:
            print(f"  [SKIP] EPCI non trouvé dans le parquet.")
            continue

        row = res.iloc[0]
        siren = row["code_siren"]
        bb = row["geometrie_bbox"]
        bbox = (bb['xmin'], bb['ymin'], bb['xmax'], bb['ymax'])

        epci_dir = Path(OUTPUT_DIR) / f"epci_{siren}"
        epci_dir.mkdir(exist_ok=True)

        # 1. Générer config
        config_path = epci_dir / "r2gg_config.json"
        generate_r2gg_config(name, siren, bbox, config_path)
        print(f"  → Config générée : {config_path}")

        # 2. Lancer r2gg
        if not shutil.which("r2gg-sql2pivot"):
            print(f"  → r2gg non trouvé. Commandes suggérées :")
            print(f"      r2gg-sql2pivot {config_path}")
            print(f"      r2gg-pivot2pgrouting {config_path}")
            continue

        print(f"  → Exécution r2gg-sql2pivot ...")
        subprocess.run(["r2gg-sql2pivot", str(config_path)], check=True)
        print(f"  → Exécution r2gg-pivot2pgrouting ...")
        subprocess.run(["r2gg-pivot2pgrouting", str(config_path)], check=True)
        print(f"  → [OK] Gold dump généré dans {epci_dir}")

    print("\n[ADMIN] Terminé.")

if __name__ == "__main__":
    main()
