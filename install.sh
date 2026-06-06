#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

install -d "$CODEX_HOME"
install -m 0644 "$ROOT_DIR/codex/kimi.config.toml" "$CODEX_HOME/kimi.config.toml"
install -m 0644 "$ROOT_DIR/codex/deepseek.config.toml" "$CODEX_HOME/deepseek.config.toml"

install -m 0755 "$ROOT_DIR/bin/codex-kimi" /usr/local/bin/codex-kimi
install -m 0755 "$ROOT_DIR/bin/codex-deepseek" /usr/local/bin/codex-deepseek

echo "Installed Codex profiles:"
echo "  $CODEX_HOME/kimi.config.toml"
echo "  $CODEX_HOME/deepseek.config.toml"
echo ""
echo "Installed wrappers:"
echo "  /usr/local/bin/codex-kimi"
echo "  /usr/local/bin/codex-deepseek"
