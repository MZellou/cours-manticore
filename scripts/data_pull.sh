#!/usr/bin/env bash
set -euo pipefail
# Pull course data from Cloudflare R2 via rclone
# Usage: ./data_pull.sh [--epci CODE]
# Needs rclone.conf with remote "manticore"
CONF="${RCLONE_CONF:-rclone.conf}"
REMOTE="${RCLONE_REMOTE:-manticore:manticore}"
DATA_DIR="${DATA_DIR:-data}"
EPCI=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --epci) EPCI="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

mkdir -p "$DATA_DIR"

if [ -n "$EPCI" ]; then
  # Selective sync: only shared + specific EPCI subdirs
  rclone --config "$CONF" copy "$REMOTE/epci.parquet" "$DATA_DIR/" --progress
  rclone --config "$CONF" copy "$REMOTE/ontologie/" "$DATA_DIR/ontologie/" --progress
  rclone --config "$CONF" copy "$REMOTE/epci_extracts/$EPCI/" "$DATA_DIR/epci_extracts/$EPCI/" --progress
  rclone --config "$CONF" copy "$REMOTE/gold_dumps/$EPCI/" "$DATA_DIR/gold_dumps/$EPCI/" --progress
else
  # Full sync
  rclone --config "$CONF" copy "$REMOTE" "$DATA_DIR/" --progress --exclude "files.txt"
fi

echo ">>> Done."