#!/usr/bin/env bash
set -euo pipefail
# Pull course data from Cloudflare R2 (bucket data-manticore)
# Only pulls EPCI extracts + ontology (not national source files)
CONF="${RCLONE_CONF:-rclone.conf}"
REMOTE="${RCLONE_REMOTE:-data-manticore:}"
LOCAL="${DATA_DIR:-data}"

mkdir -p "$LOCAL/epci_extracts" "$LOCAL/ontologie"
rclone --config "$CONF" copy "${REMOTE}epci_extracts" "$LOCAL/epci_extracts" --progress --transfers 4
rclone --config "$CONF" copy "${REMOTE}ontologie" "$LOCAL/ontologie" --progress --transfers 4
