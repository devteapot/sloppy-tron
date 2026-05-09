#!/usr/bin/env bash
set -euo pipefail

cd /workspace

platform_id="${1:-}"
if [[ -z "${platform_id}" ]]; then
  case "${ROS_DISTRO:-}" in
    jazzy) platform_id="pi5_jazzy" ;;
    humble) platform_id="jetson_humble" ;;
    *)
      echo "Unable to infer platform from ROS_DISTRO=${ROS_DISTRO:-unset}" >&2
      echo "Usage: $0 pi5_jazzy|jetson_humble" >&2
      exit 2
      ;;
  esac
fi

case "${platform_id}" in
  pi5_jazzy)
    fake_exec="fake_body_pi5_jazzy"
    bridge_exec="slop_bridge_pi5_jazzy"
    ;;
  jetson_humble)
    fake_exec="fake_body_jetson_humble"
    bridge_exec="slop_bridge_jetson_humble"
    ;;
  *)
    echo "Unsupported platform ${platform_id}" >&2
    exit 2
    ;;
esac

socket_path="/tmp/slop/sloppy-tron-${platform_id}-smoke-$$.sock"
log_dir="$(mktemp -d)"
fake_log="${log_dir}/fake_body.log"
bridge_log="${log_dir}/slop_bridge.log"
fake_pid=""
bridge_pid=""

cleanup() {
  status=$?
  if [[ -n "${bridge_pid}" ]] && kill -0 "${bridge_pid}" 2>/dev/null; then
    kill "${bridge_pid}" 2>/dev/null || true
  fi
  if [[ -n "${fake_pid}" ]] && kill -0 "${fake_pid}" 2>/dev/null; then
    kill "${fake_pid}" 2>/dev/null || true
  fi
  wait "${bridge_pid:-0}" 2>/dev/null || true
  wait "${fake_pid:-0}" 2>/dev/null || true
  rm -f "${socket_path}"
  if [[ "${status}" -ne 0 ]]; then
    echo "--- fake body log ---" >&2
    sed -n '1,200p' "${fake_log}" >&2 || true
    echo "--- SLOP bridge log ---" >&2
    sed -n '1,200p' "${bridge_log}" >&2 || true
  fi
  rm -rf "${log_dir}"
  exit "${status}"
}
trap cleanup EXIT

python3 -m pip install -e .

cd /workspace/ros
colcon build --symlink-install
set +u
source install/setup.bash
set -u
cd /workspace

rm -f "${socket_path}"

ros2 run sloppy_tron_ros_bridge "${fake_exec}" >"${fake_log}" 2>&1 &
fake_pid=$!
ros2 run sloppy_tron_ros_bridge "${bridge_exec}" \
  --ros-args \
  -p "socket_path:=${socket_path}" \
  -p "register_provider:=false" \
  >"${bridge_log}" 2>&1 &
bridge_pid=$!

wait_for_processes() {
  if ! kill -0 "${fake_pid}" 2>/dev/null; then
    echo "fake body process exited early" >&2
    return 1
  fi
  if ! kill -0 "${bridge_pid}" 2>/dev/null; then
    echo "SLOP bridge process exited early" >&2
    return 1
  fi
}

for _ in {1..50}; do
  wait_for_processes
  if [[ -S "${socket_path}" ]]; then
    break
  fi
  sleep 0.2
done

if [[ ! -S "${socket_path}" ]]; then
  echo "Timed out waiting for ${socket_path}" >&2
  exit 1
fi

wait_for_topic() {
  local topic="$1"
  for _ in {1..50}; do
    wait_for_processes
    info="$(ros2 topic info "${topic}" 2>/dev/null || true)"
    if [[ "${info}" == *"Publisher count: 1"* ]] && \
      [[ "${info}" == *"Subscription count: 1"* ]]; then
      return 0
    fi
    sleep 0.2
  done
  echo "Timed out waiting for ${topic} publisher/subscriber match" >&2
  ros2 topic info "${topic}" >&2 || true
  return 1
}

wait_for_topic /body_state
wait_for_topic /body_command

python3 /workspace/docker/ros-smoke-client.py "${socket_path}" "${platform_id}"

echo "ROS/SLOP smoke test passed for ${platform_id}"
