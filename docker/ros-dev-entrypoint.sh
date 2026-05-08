#!/usr/bin/env bash
set -e

source "/opt/ros/${ROS_DISTRO}/setup.bash"

if [[ -f /workspace/ros/install/setup.bash ]]; then
  source /workspace/ros/install/setup.bash
fi

exec "$@"
