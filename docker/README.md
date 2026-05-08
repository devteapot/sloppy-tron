# ROS Docker Dev Containers

Local macOS development uses Docker containers because macOS is not a Tier 1
ROS host platform.

Two services are defined:

- `ros-jazzy` uses `ros:jazzy-ros-base-noble` for the Raspberry Pi 5 / Ubuntu
  24.04 / ROS 2 Jazzy path.
- `ros-humble` uses `ros:humble-ros-base-jammy` for the Jetson Orin Super /
  JetPack 6 / Ubuntu 22.04 / ROS 2 Humble path.

Build the images:

```sh
docker compose build ros-jazzy
docker compose build ros-humble
```

Run the full container check for either distro:

```sh
docker compose run --rm ros-jazzy ./docker/ros-check.sh
docker compose run --rm ros-humble ./docker/ros-check.sh
```

Open an interactive shell:

```sh
docker compose run --rm ros-jazzy
docker compose run --rm ros-humble
```

The check script runs Python lint/type/tests, installs the shared
`sloppy_tron` package into the container's ROS Python environment, builds the
ROS workspace with `colcon`, and lists the bridge executables.

The compose setup keeps ROS `build/`, `install/`, and `log/` directories in
named Docker volumes per distro so Humble and Jazzy do not trample each other.
It also sets `UV_PROJECT_ENVIRONMENT=/tmp/sloppy-tron-venv` so Linux containers
do not reuse or overwrite a macOS `.venv`.
