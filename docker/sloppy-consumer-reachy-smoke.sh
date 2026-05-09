#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-mujoco}"
PORT="${REACHY_PORT:-8001}"
SOCKET_PATH="${SLOPPY_TRON_SOCKET_PATH:-/tmp/slop/sloppy-tron-body.sock}"
PROVIDERS_DIR="${SLOPPY_PROVIDER_DIR:-/root/.slop/providers}"
REACHY_LOG_FILE="${REACHY_LOG_FILE:-/tmp/reachy-mini-daemon-sloppy-smoke.log}"
PROVIDER_LOG_FILE="${SLOPPY_TRON_PROVIDER_LOG_FILE:-/tmp/sloppy-tron-provider-sloppy-smoke.log}"
SLOPPY_REPO="${SLOPPY_REPO:-/opt/sloppy}"

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

COMMON_REACHY_ARGS=(
  --fastapi-host localhost
  --fastapi-port "${PORT}"
  --no-media
  --no-wake-up-on-start
  --no-goto-sleep-on-stop
  --dataset-update-interval 0
  --log-level INFO
)

REACHY_PID=""
PROVIDER_PID=""
cleanup() {
  local rc=$?
  if [[ ${rc} -ne 0 ]]; then
    if [[ -f "${REACHY_LOG_FILE}" ]]; then
      echo "---- reachy-mini-daemon log (${REACHY_LOG_FILE}) ----" >&2
      tail -200 "${REACHY_LOG_FILE}" >&2 || true
      echo "---- end reachy-mini-daemon log ----" >&2
    fi
    if [[ -f "${PROVIDER_LOG_FILE}" ]]; then
      echo "---- sloppy-tron provider log (${PROVIDER_LOG_FILE}) ----" >&2
      tail -200 "${PROVIDER_LOG_FILE}" >&2 || true
      echo "---- end sloppy-tron provider log ----" >&2
    fi
  fi
  if [[ -n "${PROVIDER_PID}" ]]; then
    kill "${PROVIDER_PID}" >/dev/null 2>&1 || true
    wait "${PROVIDER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${REACHY_PID}" ]]; then
    kill "${REACHY_PID}" >/dev/null 2>&1 || true
    wait "${REACHY_PID}" >/dev/null 2>&1 || true
  fi
  rm -f "${PROVIDERS_DIR}/body.json" "${SOCKET_PATH}"
  exit "${rc}"
}
trap cleanup EXIT

if ! command -v reachy-mini-daemon >/dev/null 2>&1; then
  echo "reachy-mini-daemon is not installed in this environment." >&2
  exit 127
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "bun is not installed in this environment." >&2
  exit 127
fi

if [[ ! -f "${SLOPPY_REPO}/package.json" ]]; then
  echo "Sloppy repo is not mounted at ${SLOPPY_REPO}. Set SLOPPY_REPO or compose's SLOPPY_REPO variable." >&2
  exit 2
fi

mkdir -p "${PROVIDERS_DIR}" "$(dirname "${SOCKET_PATH}")"
rm -f "${PROVIDERS_DIR}/body.json" "${SOCKET_PATH}"

echo "==> Ensuring Sloppy JS dependencies in ${SLOPPY_REPO}"
(
  cd "${SLOPPY_REPO}"
  if [[ ! -d node_modules/@slop-ai/consumer ]]; then
    bun install --frozen-lockfile
  else
    bun install --frozen-lockfile --silent
  fi
)

echo "==> Starting Reachy Mini daemon (${MODE}) on localhost:${PORT}"
reachy-mini-daemon "${MODE_ARGS[@]}" "${COMMON_REACHY_ARGS[@]}" >"${REACHY_LOG_FILE}" 2>&1 &
REACHY_PID=$!

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

echo "==> Starting SloppyTron SLOP provider on ${SOCKET_PATH}"
uv run python -m sloppy_tron.provider \
  --backend reachy \
  --reachy-host localhost \
  --reachy-port "${PORT}" \
  serve-unix \
  --socket-path "${SOCKET_PATH}" \
  --register \
  >"${PROVIDER_LOG_FILE}" 2>&1 &
PROVIDER_PID=$!

python - "${PROVIDERS_DIR}/body.json" "${SOCKET_PATH}" <<'PY'
import json
import socket
import sys
import time
from pathlib import Path

provider_path = Path(sys.argv[1])
socket_path = Path(sys.argv[2])
deadline = time.time() + 30
last_error = None
while time.time() < deadline:
    try:
        if not provider_path.exists():
            last_error = f"descriptor missing: {provider_path}"
            time.sleep(0.2)
            continue
        descriptor = json.loads(provider_path.read_text())
        if descriptor.get("transport", {}).get("path") != str(socket_path):
            last_error = descriptor
            time.sleep(0.2)
            continue
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.settimeout(1)
            client.connect(str(socket_path))
        finally:
            client.close()
        print(json.dumps(descriptor, indent=2, sort_keys=True))
        raise SystemExit(0)
    except Exception as exc:  # noqa: BLE001 - smoke script prints transient failures
        last_error = str(exc)
        time.sleep(0.2)
print(f"SloppyTron provider did not become ready: {last_error}", file=sys.stderr)
raise SystemExit(1)
PY

echo "==> Exercising Sloppy ConsumerHub discovery/query/invoke path"
SLOPPY_PROVIDER_DIRS="${PROVIDERS_DIR}:/tmp/slop/providers" \
SLOPPY_REPO="${SLOPPY_REPO}" \
bun run /workspace/docker/sloppy-consumer-smoke.ts --provider-id body
