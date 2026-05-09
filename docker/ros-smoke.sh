#!/usr/bin/env bash
set -euo pipefail

cd /workspace

platform_id=""
body_mode="fake"

infer_platform_id() {
  case "${ROS_DISTRO:-}" in
    jazzy) echo "pi5_jazzy" ;;
    humble) echo "jetson_humble" ;;
    *)
      echo "Unable to infer platform from ROS_DISTRO=${ROS_DISTRO:-unset}" >&2
      echo "Usage: $0 [pi5_jazzy|jetson_humble] [fake|baseline]" >&2
      echo "       $0 [fake|baseline]" >&2
      exit 2
      ;;
  esac
}

case "${1:-}" in
  "")
    platform_id="$(infer_platform_id)"
    ;;
  fake|baseline)
    platform_id="$(infer_platform_id)"
    body_mode="$1"
    ;;
  pi5_jazzy|jetson_humble)
    platform_id="$1"
    body_mode="${2:-fake}"
    ;;
  *)
    echo "Unsupported platform/body mode ${1}" >&2
    echo "Usage: $0 [pi5_jazzy|jetson_humble] [fake|baseline]" >&2
    echo "       $0 [fake|baseline]" >&2
    exit 2
    ;;
esac

case "${platform_id}:${body_mode}" in
  pi5_jazzy:fake)
    body_package="sloppy_tron_ros_bridge"
    body_exec="fake_body_pi5_jazzy"
    bridge_exec="slop_bridge_pi5_jazzy"
    ;;
  jetson_humble:fake)
    body_package="sloppy_tron_ros_bridge"
    body_exec="fake_body_jetson_humble"
    bridge_exec="slop_bridge_jetson_humble"
    ;;
  pi5_jazzy:baseline)
    body_package="sloppy_tron_body_baseline"
    body_exec="baseline_body_pi5_jazzy"
    bridge_exec="slop_bridge_pi5_jazzy"
    ;;
  jetson_humble:baseline)
    body_package="sloppy_tron_body_baseline"
    body_exec="baseline_body_jetson_humble"
    bridge_exec="slop_bridge_jetson_humble"
    ;;
  *)
    echo "Unsupported platform/body mode ${platform_id}:${body_mode}" >&2
    exit 2
    ;;
esac

case "${platform_id}" in
  pi5_jazzy) smoke_ros_domain_id="${SLOPPY_TRON_SMOKE_ROS_DOMAIN_ID:-142}" ;;
  jetson_humble) smoke_ros_domain_id="${SLOPPY_TRON_SMOKE_ROS_DOMAIN_ID:-143}" ;;
esac

export ROS_DOMAIN_ID="${smoke_ros_domain_id}"
mkdir -p /tmp/slop
socket_path="$(mktemp -u "/tmp/slop/sloppy-tron-${platform_id}-smoke-XXXXXX.sock")"
log_dir="$(mktemp -d)"
body_log="${log_dir}/${body_mode}_body.log"
bridge_log="${log_dir}/slop_bridge.log"
body_pid=""
bridge_pid=""

cleanup() {
  status=$?
  if [[ -n "${bridge_pid}" ]] && kill -0 "${bridge_pid}" 2>/dev/null; then
    kill "${bridge_pid}" 2>/dev/null || true
  fi
  if [[ -n "${body_pid}" ]] && kill -0 "${body_pid}" 2>/dev/null; then
    kill "${body_pid}" 2>/dev/null || true
  fi
  wait "${bridge_pid:-0}" 2>/dev/null || true
  wait "${body_pid:-0}" 2>/dev/null || true
  rm -f "${socket_path}"
  if [[ "${status}" -ne 0 ]]; then
    echo "--- ${body_mode} body log ---" >&2
    sed -n '1,200p' "${body_log}" >&2 || true
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

ros2 run "${body_package}" "${body_exec}" >"${body_log}" 2>&1 &
body_pid=$!
ros2 run sloppy_tron_ros_bridge "${bridge_exec}" \
  --ros-args \
  -p "socket_path:=${socket_path}" \
  -p "register_provider:=false" \
  >"${bridge_log}" 2>&1 &
bridge_pid=$!

wait_for_processes() {
  if ! kill -0 "${body_pid}" 2>/dev/null; then
    echo "${body_mode} body process exited early" >&2
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

echo "ROS/SLOP smoke test passed for ${platform_id} (${body_mode})"
