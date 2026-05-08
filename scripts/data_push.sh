#!/usr/bin/env bash
set -euo pipefail
# Push course data to Cloudflare R2 (instructor only)
# Syncs data + generates files.txt manifest for pull script
CONF="${RCLONE_CONF:-rclone.conf}"
LOCAL="${DATA_DIR:-data}"
REMOTE="${RCLONE_REMOTE:-manticore:manticore/}"

# Sync data dirs
for dir in epci_extracts ontologie gold_dumps; do
  [ -d "$LOCAL/$dir" ] || continue
  rclone --config "$CONF" copy "$LOCAL/$dir" "${REMOTE}$dir" --progress --transfers 4
done
[ -f "$LOCAL/epci.parquet" ] && rclone --config "$CONF" copy "$LOCAL/epci.parquet" "$REMOTE" --progress

# Generate and upload manifest
cd "$LOCAL"
find . -type f \( -name '*.parquet' -o -name '*.sql' -o -name '*.csv' \) -printf '%P\n' | sort > ../files.txt
cd ..
echo ">>> Uploading files.txt ($(wc -l < files.txt) files)"
rclone --config "$CONF" copy files.txt "$REMOTE" --progress
