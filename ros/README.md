# ROS 2 Workspace

Target baseline:

- Raspberry Pi 5
- Ubuntu 24.04
- ROS 2 Jazzy LTS

Planned/current node graph:

- fake body state publisher
- deterministic Reachy-compatible baseline body publisher
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

# Fast fake-backend bridge smoke.
docker compose run --rm ros-jazzy ./docker/ros-smoke.sh fake
docker compose run --rm ros-humble ./docker/ros-smoke.sh fake

# Deterministic ROS body baseline smoke.
docker compose run --rm ros-jazzy ./docker/ros-smoke.sh baseline
docker compose run --rm ros-humble ./docker/ros-smoke.sh baseline
```

These run the same shared code through ROS 2 Jazzy and ROS 2 Humble containers.
See `docker/README.md` for image details and interactive shell commands.

## Current Bridge Scaffold

The ROS workspace now has three package roles:

- `ros/src/sloppy_tron_ros_bridge` hosts the SLOP bridge plus the lightweight
  fake body node.
- `ros/src/sloppy_tron_body_baseline` hosts a deterministic, Reachy-compatible
  kinematic baseline body. It publishes the same semantic `body_state` JSON as
  other body backends plus `sensor_msgs/JointState` on `joint_states`. It is the
  open baseline for SloppyTron's own ROS body graph; Reachy MuJoCo remains the
  vendor oracle, not the substrate we depend on.
- `ros/src/sloppy_tron_description` hosts the first custom SloppyTron v0 visual
  and kinematic description: Reachy-inspired companion proportions using the
  Sloppy mascot from `~/dev/slop/logo/sloppy.svg` as the visual reference.

It adds these initial node roles:

- `fake_body_*` owns the fake backend, publishes semantic body state on
  `body_state`, and executes semantic commands from `body_command`.
- `baseline_body_*` owns the deterministic ROS baseline, publishes semantic body
  state on `body_state`, executes semantic commands from `body_command`, and
  publishes kinematic joints on `joint_states`.
- `slop_bridge_*` subscribes to `body_state`, exposes the `body` SLOP provider
  on a local Unix socket, and publishes SLOP affordance invocations as semantic
  commands on `body_command`.

Platform-specific entrypoints:

| Platform | ROS | Entrypoints | Launch |
| --- | --- | --- | --- |
| Raspberry Pi 5 / Ubuntu 24.04 | Jazzy | `fake_body_pi5_jazzy`, `baseline_body_pi5_jazzy`, `slop_bridge_pi5_jazzy` | `sloppy_tron_ros_bridge/pi5_jazzy.launch.py`, `sloppy_tron_body_baseline/pi5_jazzy.launch.py` |
| Jetson Orin Super / JetPack 6 / Ubuntu 22.04 | Humble | `fake_body_jetson_humble`, `baseline_body_jetson_humble`, `slop_bridge_jetson_humble` | `sloppy_tron_ros_bridge/jetson_humble.launch.py`, `sloppy_tron_body_baseline/jetson_humble.launch.py` |

The generic `fake_body`, `baseline_body`, and `slop_bridge` commands currently
default to the Pi 5 / Jazzy profile.

The v0 visual description can be inspected from a full ROS desktop install with:

```sh
ros2 launch sloppy_tron_description view_sloppy_tron_v0.launch.py
```

The generated low-poly meshes are reference geometry only. Final printable CAD
belongs under `cad/sloppy_tron_v0/` and should keep the URDF joint/link names so
the SLOP `/body` contract stays invariant while the exterior evolves.

The command/state topics are a development bridge, not the final low-level
hardware interface. The command envelope stays semantic (`wake`, `sleep`,
`look_at_angles`, `gesture`, `capture_frame`, `enable_motion`,
`emergency_stop`) so raw motor control remains outside the Sloppy-facing
provider.

The Docker smoke test starts `fake_body_*` or `baseline_body_*` plus
`slop_bridge_*`, waits for the ROS topic endpoints to connect, invokes the
provider over its Unix SLOP socket, and verifies the resulting pose through SLOP
state. Use `./docker/ros-smoke.sh baseline` for the deterministic body graph and
`./docker/ros-smoke.sh fake` for the lightweight fake backend.

The ROS package also includes a `launch_testing` integration test at
`ros/src/sloppy_tron_ros_bridge/test/test_slop_bridge_integration.py`. It
launches the fake body and SLOP bridge under `colcon test`, invokes
`enable_motion` and `look_at_angles` through the Unix SLOP socket, and verifies
the platform metadata and final fake pose through SLOP state.

Example Pi 5 / Jazzy workflow:

```sh
cd /Users/carlid/dev/sloppy-tron
uv sync
source /opt/ros/jazzy/setup.bash
python3 -m pip install -e .
cd ros
colcon build --symlink-install
source install/setup.bash
colcon test --packages-select sloppy_tron_ros_bridge
colcon test-result --verbose
ros2 launch sloppy_tron_body_baseline pi5_jazzy.launch.py
# or the fake bridge-only body:
# ros2 launch sloppy_tron_ros_bridge pi5_jazzy.launch.py
```

Example Jetson / Humble workflow:

```sh
cd /Users/carlid/dev/sloppy-tron
source /opt/ros/humble/setup.bash
python3 -m pip install -e .
cd ros
colcon build --symlink-install
source install/setup.bash
colcon test --packages-select sloppy_tron_ros_bridge
colcon test-result --verbose
ros2 launch sloppy_tron_body_baseline jetson_humble.launch.py
# or the fake bridge-only body:
# ros2 launch sloppy_tron_ros_bridge jetson_humble.launch.py
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
