#!/usr/bin/env bash
# Builds Bhavna-mac.zip: code + docs + the Mac model folders. No git, no venv, no stats. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-$HOME/Downloads/Bhavna-mac.zip}"
rm -f "$OUT"
zip -qr "$OUT" README.md CLAUDE.md macos tools tests docs models/apex-mlx-q8 -x '*.venv*' '*__pycache__*' '*.DS_Store' 'macos/.venv/*'
echo "wrote $OUT ($(du -h "$OUT" | cut -f1))"
