# SloppyTron

SloppyTron is the local robot body project for Sloppy: a small, home-local,
Reachy-inspired embodied presence that exposes its senses, motion, safety, and
privacy state through SLOP.

The first version is deliberately tiny: a Raspberry Pi 5, two-servo pan/tilt
head, camera, microphone, speaker, ROS 2 body graph, and a SLOP adapter that a
Sloppy instance can consume.

## Shape

```text
Sloppy session
  |
  v
body SLOP provider
  |
  v
ROS 2 adapter node
  |
  v
ROS 2 body graph on Pi 5
  |
  +-- servo bridge
  +-- camera/audio nodes
  +-- gesture action server
  +-- safety watchdog
```

## Repository Layout

- `docs/spec.md` — current SloppyTron specification.
- `ros/` — ROS 2 workspace notes and the current `ament_python` bridge
  package.
- `provider/` — SLOP adapter notes for the Python provider built on the SLOP
  Python SDK.
- `src/sloppy_tron/provider/` — current `slop-ai` SDK adapter, provider
  contract, and fake backend.
- `src/sloppy_tron/ros_bridge/` — ROS/SLOP bridge core shared by tests and ROS
  nodes.
- `tests/` — provider contract, SDK adapter, and fake backend tests.
- `firmware/` — microcontroller or servo bridge firmware.
- `cad/` — printable parts, mounts, and mechanical references.
- `bom/` — parts list, wiring, power, and purchasing notes.
- `config/` — example Sloppy/provider configuration.
- `docker/` — local macOS ROS dev containers for Humble and Jazzy.

## Dependency Direction

SloppyTron is separate from Sloppy. The hardware stack should not depend on
Sloppy internals. The clean dependency boundary is:

```text
sloppy-tron
  -> exposes a SLOP provider

sloppy
  -> consumes that provider
```

For body-local agent experiments, this package can also depend on the public
Sloppy GitHub repo and run a local Sloppy instance that consumes the same body
provider.

## First Milestone

- Pi 5
- camera
- mic and speaker
- two-servo pan/tilt head
- servo controller or microcontroller bridge
- dedicated servo power rail and reachable motor cutoff
- visible listening/mute indicator
- ROS 2 fake and real body graph
- SLOP adapter exposing a `body` provider

Success means Sloppy can wake the body, look around, nod, idle, sleep, speak,
request a camera frame explicitly, and always observe safety/privacy state.

## Platform Bridges

The SLOP contract and semantic bridge core are shared. The ROS edge has separate
entrypoints for the first two likely platforms:

- Raspberry Pi 5: `slop_bridge_pi5_jazzy` and `fake_body_pi5_jazzy`
  for Ubuntu 24.04, Python 3.12, and ROS 2 Jazzy.
- Jetson Orin Super: `slop_bridge_jetson_humble` and
  `fake_body_jetson_humble` for JetPack 6, Ubuntu 22.04, Python 3.10, and
  ROS 2 Humble.

For local macOS development, use the Docker services in `compose.yaml`:

```sh
docker compose run --rm ros-jazzy ./docker/ros-check.sh
docker compose run --rm ros-humble ./docker/ros-check.sh
docker compose run --rm ros-jazzy ./docker/ros-smoke.sh
docker compose run --rm ros-humble ./docker/ros-smoke.sh
```

## Status

Software scaffold in progress. The repo currently has a fake Python `body`
provider using the `slop-ai` SDK, a Reachy Mini daemon backend for mockup/MuJoCo
simulation behind the same SLOP consumer contract, shared ROS bridge core logic,
a first `ament_python` ROS package, and local Docker checks for Jazzy and Humble.
No real hardware-control backend is implemented yet.
