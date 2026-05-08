# Sloppy-Tron

Sloppy-Tron is the local robot body project for Sloppy: a small, home-local,
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

- `docs/spec.md` — current Sloppy-Tron specification.
- `ros/` — ROS 2 workspace notes and future packages.
- `provider/` — SLOP adapter/provider notes and future TypeScript code.
- `firmware/` — microcontroller or servo bridge firmware.
- `cad/` — printable parts, mounts, and mechanical references.
- `bom/` — parts list, wiring, power, and purchasing notes.
- `config/` — example Sloppy/provider configuration.
- `src/` — shared TypeScript package entrypoint and future helpers.

## Dependency Direction

Sloppy-Tron is separate from Sloppy. The hardware stack should not depend on
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

## Status

Pre-build planning. No hardware-control code is implemented yet.
