# Docker Dev Containers

Local macOS development uses Docker containers because macOS is not a Tier 1
ROS host platform.

Two ROS services are defined:

- `ros-jazzy` uses `ros:jazzy-ros-base-noble` for the Raspberry Pi 5 / Ubuntu
  24.04 / ROS 2 Jazzy path.
- `ros-humble` uses `ros:humble-ros-base-jammy` for the Jetson Orin Super /
  JetPack 6 / Ubuntu 22.04 / ROS 2 Humble path.

One Reachy end-to-end service is also defined:

- `reachy-e2e` uses `python:3.12-bookworm`, installs the pinned upstream
  `reachy_mini[mujoco]` daemon, MuJoCo 3.3.0, GStreamer introspection libs, and
  software headless GL (`MUJOCO_GL=osmesa`). It is for validating the
  SloppyTron `ReachyDaemonBackend` against the real upstream FastAPI daemon.

Build the images:

```sh
docker compose build reachy-e2e
docker compose build ros-jazzy
docker compose build ros-humble
```

Run the Reachy daemon end-to-end smoke in the container:

```sh
# Fast daemon/API integration, no physics.
docker compose run --rm reachy-e2e ./docker/reachy-e2e-check.sh mockup

# Full upstream daemon + MuJoCo + SloppyTron Reachy backend path.
docker compose run --rm reachy-e2e ./docker/reachy-e2e-check.sh mujoco
```

The Reachy smoke script starts `reachy-mini-daemon`, waits for
`/api/daemon/status`, connects through `ReachyDaemonBackend`, invokes
`enable_motion`, invokes `look_at_angles`, and verifies that the final state still
has the standard SLOP body-provider shape. The service defines a `${REACHY_PORT}`
(default `8001`) port mapping; use `docker compose run --service-ports` when
running a long-lived custom daemon command if you want to inspect the API from
the host.

Run the full container check for either ROS distro:

```sh
docker compose run --rm ros-jazzy ./docker/ros-check.sh
docker compose run --rm ros-humble ./docker/ros-check.sh
```

Run the runtime smoke test for either distro:

```sh
docker compose run --rm ros-jazzy ./docker/ros-smoke.sh
docker compose run --rm ros-humble ./docker/ros-smoke.sh
```

The smoke script installs the shared package into the ROS Python environment,
builds the ROS workspace, starts the fake body and SLOP bridge nodes, waits for
the `body_state` and `body_command` topic endpoints to match, connects through
the bridge's Unix SLOP socket, invokes `enable_motion`, invokes
`look_at_angles`, and verifies the final pose through SLOP state.

Open an interactive shell:

```sh
docker compose run --rm reachy-e2e
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

The Reachy image pins the upstream daemon through the `REACHY_MINI_SPEC` build
argument, defaulting to `reachy_mini[mujoco]==1.7.1`:

```sh
REACHY_MINI_SPEC='reachy_mini[mujoco]==1.7.1' docker compose build reachy-e2e
```
