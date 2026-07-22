#!/usr/bin/env bash
# NousAI Phase 1 installer (Linux/macOS).
# Copies the skin and persona into the Hermes home directory — never touches the repo.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_DIR="${HERMES_HOME:-$HOME/.hermes}"

echo "Installing NousAI Phase 1 into: $HERMES_DIR"
mkdir -p "$HERMES_DIR/skins"

cp "$SRC/skins/nousai.yaml" "$HERMES_DIR/skins/nousai.yaml"
echo "  ✓ skin  → $HERMES_DIR/skins/nousai.yaml"

if [ -f "$HERMES_DIR/SOUL.md" ]; then
  BACKUP="$HERMES_DIR/SOUL.md.bak-$(date +%Y%m%d%H%M%S)"
  cp "$HERMES_DIR/SOUL.md" "$BACKUP"
  echo "  • existing SOUL.md backed up → $BACKUP"
fi
cp "$SRC/SOUL.md" "$HERMES_DIR/SOUL.md"
echo "  ✓ persona → $HERMES_DIR/SOUL.md"

if [ ! -f "$HERMES_DIR/config.yaml" ]; then
  printf 'display:\n  skin: nousai\ndashboard:\n  theme: nousai\n' > "$HERMES_DIR/config.yaml"
  echo "  ✓ config  → $HERMES_DIR/config.yaml (display.skin + dashboard.theme: nousai)"
else
  echo "  • config.yaml already exists — left untouched."
  echo "    Activate the skin by running '/skin nousai' inside Hermes (persists automatically),"
  echo "    or set 'display.skin: nousai' and 'dashboard.theme: nousai' in $HERMES_DIR/config.yaml yourself."
fi

echo "Done. Start hermes and the banner should greet you as NousAI."
