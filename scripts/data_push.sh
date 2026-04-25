#!/usr/bin/env bash
set -euo pipefail
# Push course data to Cloudflare R2 (instructor only)
CONF="${RCLONE_CONF:-rclone.conf}"
LOCAL="${DATA_DIR:-data}"
REMOTE="${RCLONE_REMOTE:-manticore:data}"

rclone --config "$CONF" copy "$LOCAL" "$REMOTE" --progress --transfers 4
