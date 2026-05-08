#!/usr/bin/env bash
set -euo pipefail
# Pull course data from public Cloudflare R2 bucket
# Usage: ./data_pull.sh [--epci CODE]
R2_BASE="${R2_BASE_URL:-https://pub-957b1b37b8354b00bdee80b8b70f7e50.r2.dev}"
DATA_DIR="${DATA_DIR:-data}"
EPCI=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --epci) EPCI="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

mkdir -p "$DATA_DIR"

echo ">>> Fetching manifest..."
mapfile -t FILES < <(curl -fsSL "${R2_BASE}/files.txt")

echo ">>> Downloading $((${#FILES[@]} - 1)) files..."
for f in "${FILES[@]}"; do
  [ -z "$f" ] && continue

  # Filter by EPCI if specified
  if [ -n "$EPCI" ]; then
    case "$f" in
      epci.parquet|ontologie/*) ;;
      epci_extracts/"$EPCI"/*|gold_dumps/"$EPCI"/*) ;;
      *) continue ;;
    esac
  fi

  dir="$DATA_DIR/$(dirname "$f")"
  mkdir -p "$dir"
  echo "  $f"
  curl -fsSL "${R2_BASE}/${f}" -o "$DATA_DIR/$f"
done

echo ">>> Done."
