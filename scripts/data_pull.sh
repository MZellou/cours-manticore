#!/usr/bin/env bash
set -euo pipefail
# Pull course data from public Cloudflare R2 bucket (no auth needed)
R2_BASE="${R2_BASE_URL:-https://pub-XXXX.r2.dev}"
LOCAL="${DATA_DIR:-data}"
PARALLEL="${PARALLEL:-4}"

mkdir -p "$LOCAL/epci_extracts" "$LOCAL/ontologie" "$LOCAL/gold_dumps"

# EPCI geometries
[ -f "$LOCAL/epci.parquet" ] || curl -fSL "$R2_BASE/epci.parquet" -o "$LOCAL/epci.parquet"

# Ontology files
echo ">>> Downloading ontology..."
curl -fSL "$R2_BASE/ontologie/" -o /dev/null 2>/dev/null && \
  echo "Note: R2 public buckets don't support directory listing." && \
  echo "Run: curl -fSL $R2_BASE/ontologie/<filename> -o $LOCAL/ontologie/<filename>" || true

# EPCI extracts — each EPCI has its own subdir
# This is best-effort: we list known SIREN codes
EPCI_CODES=(
  200023414 200040715 200046977 200067106 200067205
  200084952 200093201 242900314 243300316 243700754
  244400404 245900428 246700488
)

echo ">>> Downloading EPCI extracts..."
for code in "${EPCI_CODES[@]}"; do
  mkdir -p "$LOCAL/epci_extracts/$code"
  for table in administratif_hydrographique aerodrome borne_limite_propriete \
    borne_repere_nivellement broupe_routier_communaute_commune \
    cable_souterrain_canalisation equipement_de_transport \
    lieu_dit_habite ligne_electrique_aerienne noeud_reseau_routier \
    parcelle_piece point_d_eau service_public \
    signalisation_routiere surface_activite surface_hydrographique \
    troncon_de_route; do
    # Try both .parquet and .parquet.enc if encrypted
    for ext in .parquet .parquet.enc; do
      url="$R2_BASE/epci_extracts/$code/$table$ext"
      if curl -fsSL "$url" -o "$LOCAL/epci_extracts/$code/$table$ext" 2>/dev/null; then
        echo "  ✓ $code/$table$ext"
      fi
    done
  done &
  # Limit parallel downloads
  if (( $(jobs -r | wc -l) >= PARALLEL )); then wait -n; fi
done
wait
echo ">>> Done."
