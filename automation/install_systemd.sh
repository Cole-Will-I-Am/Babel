#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

install -m 0644 "$ROOT_DIR/systemd/babel-autonomy.service" "$SYSTEMD_DIR/babel-autonomy.service"
install -m 0644 "$ROOT_DIR/systemd/babel-autonomy.timer" "$SYSTEMD_DIR/babel-autonomy.timer"

systemctl daemon-reload
systemctl enable --now babel-autonomy.timer

echo "Installed and enabled babel-autonomy.timer"
systemctl list-timers --all --no-pager | rg babel-autonomy || true
