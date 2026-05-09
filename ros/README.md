# ROS 2 Workspace

Target baseline:

- Raspberry Pi 5
- Ubuntu 24.04
- ROS 2 Jazzy LTS

Planned node graph:

- fake body state publisher
- servo bridge node
- camera state node
- audio state node
- gesture action server
- safety watchdog node
- SLOP adapter node

The ROS graph is the body-internal robotics substrate. Sloppy should see the
curated SLOP provider, not arbitrary ROS topics.

## Local Docker Development

On macOS, use the Docker services from the repo root:

```sh
docker compose run --rm ros-jazzy ./docker/ros-check.sh
docker compose run --rm ros-humble ./docker/ros-check.sh
docker compose run --rm ros-jazzy ./docker/ros-smoke.sh
docker compose run --rm ros-humble ./docker/ros-smoke.sh
```

These run the same shared code through ROS 2 Jazzy and ROS 2 Humble containers.
See `docker/README.md` for image details and interactive shell commands.

## Current Bridge Scaffold

The first ROS package lives at `ros/src/sloppy_tron_ros_bridge`.

It adds two initial node roles:

- `fake_body_*` owns the fake backend, publishes semantic body state on
  `body_state`, and executes semantic commands from `body_command`.
- `slop_bridge_*` subscribes to `body_state`, exposes the `body` SLOP provider
  on a local Unix socket, and publishes SLOP affordance invocations as semantic
  commands on `body_command`.

Platform-specific entrypoints:

| Platform | ROS | Entrypoints | Launch |
| --- | --- | --- | --- |
| Raspberry Pi 5 / Ubuntu 24.04 | Jazzy | `fake_body_pi5_jazzy`, `slop_bridge_pi5_jazzy` | `pi5_jazzy.launch.py` |
| Jetson Orin Super / JetPack 6 / Ubuntu 22.04 | Humble | `fake_body_jetson_humble`, `slop_bridge_jetson_humble` | `jetson_humble.launch.py` |

The generic `fake_body` and `slop_bridge` commands currently default to the
Pi 5 / Jazzy profile.

The command/state topics are a development bridge, not the final low-level
hardware interface. The command envelope stays semantic (`wake`, `sleep`,
`look_at_angles`, `gesture`, `capture_frame`, `enable_motion`,
`emergency_stop`) so raw motor control remains outside the Sloppy-facing
provider.

The Docker smoke test starts `fake_body_*` and `slop_bridge_*`, waits for the
ROS topic endpoints to connect, invokes the provider over its Unix SLOP socket,
and verifies the resulting fake pose through SLOP state.

Example Pi 5 / Jazzy workflow:

```sh
cd /Users/carlid/dev/sloppy-tron
uv sync
source /opt/ros/jazzy/setup.bash
python3 -m pip install -e .
cd ros
colcon build --symlink-install
source install/setup.bash
ros2 launch sloppy_tron_ros_bridge pi5_jazzy.launch.py
```

Example Jetson / Humble workflow:

```sh
cd /Users/carlid/dev/sloppy-tron
source /opt/ros/humble/setup.bash
python3 -m pip install -e .
cd ros
colcon build --symlink-install
source install/setup.bash
ros2 launch sloppy_tron_ros_bridge jetson_humble.launch.py
```

The editable install makes the shared `sloppy_tron` provider package visible to
ROS's Python environment. If this becomes annoying on the Pi, split the shared
provider package into the ROS workspace as its own `ament_python` package.

`slop_bridge` parameters:

- `platform_id` is `pi5_jazzy` or `jetson_humble`
- `socket_path` defaults to a platform-specific socket under `/tmp/slop`
- `register_provider` defaults to `true`
- `state_topic` defaults to `body_state`
- `command_topic` defaults to `body_command`
