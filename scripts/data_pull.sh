#!/usr/bin/env bash
set -euo pipefail
# Pull course data from Cloudflare R2 via rclone (requires R2 creds in .env)
DATA_DIR="${DATA_DIR:-data}"
BUCKET="${R2_BUCKET:-cours-manticore}"
mkdir -p "$DATA_DIR"

# Configure rclone on-the-fly from env vars
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}"
export RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true

echo ">>> Syncing r2:${BUCKET} → ${DATA_DIR}/"
rclone sync "R2:${BUCKET}" "$DATA_DIR" --progress --transfers 4
echo ">>> Done."
