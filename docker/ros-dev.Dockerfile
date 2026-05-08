ARG ROS_IMAGE=ros:jazzy-ros-base-noble
FROM ${ROS_IMAGE}

ARG ROS_DISTRO=jazzy
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=${ROS_DISTRO}
ENV PIP_BREAK_SYSTEM_PACKAGES=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    ca-certificates \
    curl \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-yaml \
    python3-rosdep \
    python3-setuptools \
    python3-venv \
    python3-wheel \
    "ros-${ROS_DISTRO}-launch-ros" \
    "ros-${ROS_DISTRO}-rclpy" \
    "ros-${ROS_DISTRO}-std-msgs" \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir uv
RUN rosdep init 2>/dev/null || true

COPY docker/ros-dev-entrypoint.sh /ros-dev-entrypoint.sh
RUN chmod +x /ros-dev-entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/ros-dev-entrypoint.sh"]
CMD ["bash"]
