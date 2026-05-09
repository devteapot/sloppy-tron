#!/usr/bin/env bash
set -euo pipefail

cd /workspace

uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/sloppy_tron/provider src/sloppy_tron/ros_bridge src/sloppy_tron/ros_body_baseline
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest

python3 -m pip install -e .

cd /workspace/ros
colcon build --symlink-install
set +u
source install/setup.bash
set -u
ros2 pkg executables sloppy_tron_ros_bridge
ros2 pkg executables sloppy_tron_body_baseline
colcon test --packages-select sloppy_tron_ros_bridge --event-handlers console_direct+
colcon test-result --verbose
