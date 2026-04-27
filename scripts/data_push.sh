#!/usr/bin/env bash
set -euo pipefail
# Push course data to Cloudflare R2 (bucket data-manticore, instructor only)
# Syncs: epci_extracts, ontologie, gold_dumps, epci.parquet
CONF="${RCLONE_CONF:-rclone.conf}"
LOCAL="${DATA_DIR:-data}"
REMOTE="${RCLONE_REMOTE:-data-manticore:}"

for dir in epci_extracts ontologie gold_dumps; do
  [ -d "$LOCAL/$dir" ] || continue
  rclone --config "$CONF" copy "$LOCAL/$dir" "${REMOTE}$dir" --progress --transfers 4
done
[ -f "$LOCAL/epci.parquet" ] && rclone --config "$CONF" copy "$LOCAL/epci.parquet" "$REMOTE" --progress
