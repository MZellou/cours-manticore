#!/usr/bin/env bash
set -euo pipefail
# Pull course data from Cloudflare R2 via rclone
ENV_FILE="${ENV_FILE:-.env}"
[ -f "$ENV_FILE" ] && set -a && source "$ENV_FILE" && set +a

CONF="${RCLONE_CONF:-rclone.conf}"
REMOTE="${RCLONE_REMOTE:-manticore:manticore}"
DATA_DIR="${DATA_DIR:-data}"

mkdir -p "$DATA_DIR"
echo ">>> Syncing ${REMOTE} → ${DATA_DIR}/"
rclone --config "$CONF" sync "$REMOTE" "$DATA_DIR" --progress --transfers 4
echo ">>> Done."
