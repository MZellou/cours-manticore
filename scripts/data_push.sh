#!/usr/bin/env bash
set -euo pipefail
# Push course data to Cloudflare R2 (bucket data-manticore, instructor only)
# Only pushes EPCI extracts + ontology (not national source files)
CONF="${RCLONE_CONF:-rclone.conf}"
LOCAL="${DATA_DIR:-data}"
REMOTE="${RCLONE_REMOTE:-data-manticore:}"

rclone --config "$CONF" copy "$LOCAL/epci_extracts" "${REMOTE}epci_extracts" --progress --transfers 4
rclone --config "$CONF" copy "$LOCAL/ontologie" "${REMOTE}ontologie" --progress --transfers 4
