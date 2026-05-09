#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mujoco}"
PORT="${REACHY_PORT:-8001}"
LOG_FILE="${REACHY_LOG_FILE:-/tmp/reachy-mini-daemon-smoke.log}"

if ! command -v reachy-mini-daemon >/dev/null 2>&1; then
  echo "reachy-mini-daemon is not installed. Install pollen-robotics/reachy_mini with the mujoco extra first." >&2
  echo "Example: uv tool install 'reachy_mini[mujoco]'" >&2
  exit 127
fi

case "${MODE}" in
  mujoco)
    MODE_ARGS=(--sim --headless --scene empty)
    ;;
  mockup|mockup-sim)
    MODE_ARGS=(--mockup-sim)
    ;;
  *)
    echo "usage: $0 [mujoco|mockup]" >&2
    exit 2
    ;;
esac

COMMON_ARGS=(
  --fastapi-host localhost
  --fastapi-port "${PORT}"
  --no-media
  --no-wake-up-on-start
  --no-goto-sleep-on-stop
  --dataset-update-interval 0
  --log-level INFO
)

echo "Starting Reachy Mini daemon (${MODE}) on localhost:${PORT}..."
reachy-mini-daemon "${MODE_ARGS[@]}" "${COMMON_ARGS[@]}" >"${LOG_FILE}" 2>&1 &
DAEMON_PID=$!
trap 'kill "${DAEMON_PID}" >/dev/null 2>&1 || true' EXIT

python - "${PORT}" <<'PY'
import json
import sys
import time
import urllib.request

port = int(sys.argv[1])
url = f"http://localhost:{port}/api/daemon/status"
deadline = time.time() + 60
last_error = None
while time.time() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            status = json.loads(response.read().decode("utf-8"))
        if status.get("state") == "running":
            print(json.dumps(status, indent=2, sort_keys=True))
            raise SystemExit(0)
        last_error = status
    except Exception as exc:  # noqa: BLE001 - smoke script prints transient failures
        last_error = str(exc)
    time.sleep(1)
print(f"Reachy daemon did not become ready: {last_error}", file=sys.stderr)
raise SystemExit(1)
PY

uv run python docker/reachy-smoke-client.py --host localhost --port "${PORT}"
