#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mujoco}"

echo "==> Reachy offline contract tests"
uv run pytest -q tests/test_reachy_backend.py

echo "==> Reachy daemon end-to-end smoke (${MODE})"
./docker/reachy-mujoco-smoke.sh "${MODE}"
