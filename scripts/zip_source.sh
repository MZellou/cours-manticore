#!/bin/bash
# Zip les sources du projet (sans data, .venv, builds...)
set -euo pipefail
OUTPUT="${1:-archive/cours-manticore-source.zip}"
mkdir -p "$(dirname "$OUTPUT")"

zip -r "$OUTPUT" . \
  -x "data/*" \
  -x ".venv/*" \
  -x "_site/*" \
  -x ".quarto/*" \
  -x ".git/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x ".pytest_cache/*" \
  -x "route-graph-generator/*" \
  -x "archive/*" \
  -x ".wrangler/*" \
  -x ".opencode/*" \
  -x ".env" \
  -x "rclone.conf" \
  -x ".DS_Store" \
  -x "Thumbs.db" \
  -x "_extensions/*" \
  -x "*.zip"

echo "✅ Zip créé : $(realpath "$OUTPUT")"
echo "   Taille : $(du -h "$OUTPUT" | cut -f1)"
