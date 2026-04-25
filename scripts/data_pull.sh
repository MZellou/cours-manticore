#!/usr/bin/env bash
set -euo pipefail
# Pull course data from Cloudflare R2
CONF="${RCLONE_CONF:-rclone.conf}"
REMOTE="${RCLONE_REMOTE:-manticore:data}"
LOCAL="${DATA_DIR:-data}"

rclone --config "$CONF" copy "$REMOTE" "$LOCAL" --progress --transfers 4
