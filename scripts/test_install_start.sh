#!/usr/bin/env bash
# Test that install.sh and start.sh --check-only succeed.
# Run from the repository root: ./scripts/test_install_start.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -f "$REPO_ROOT/install.sh" ] || [ ! -f "$REPO_ROOT/start.sh" ]; then
    echo "Error: Run this script from the repo root. install.sh and start.sh not found."
    exit 1
fi

# Ensure config exists so install.sh is non-interactive
if [ ! -f "$REPO_ROOT/config.json" ] && [ -f "$REPO_ROOT/config.example.json" ]; then
    cp "$REPO_ROOT/config.example.json" "$REPO_ROOT/config.json"
    echo "Copied config.example.json to config.json for non-interactive install."
fi

echo "Running ./install.sh ..."
./install.sh

echo "Running ./start.sh --check-only ..."
./start.sh --check-only

echo "OK: install and start --check-only succeeded."
