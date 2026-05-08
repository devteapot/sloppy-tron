# Sloppy-Tron

Sloppy-Tron is the future-design specification for building a local embodied
Sloppy presence using Reachy Mini as the baseline, without waiting for official
hardware delivery.

It is not implemented runtime behavior yet.

## Goal

Build a desktop/home robot body that gives Sloppy physical presence:

- local camera, microphone, and speaker
- expressive head movement
- simple gestures such as nods, tilts, idle breathing, attentive tracking, and
  sleep/wake transitions
- observable body state exposed as SLOP state
- motion and media controls exposed as contextual SLOP affordances
- safety and privacy controls visible before any risky action

Sloppy-Tron should begin as a custom body with a stable Sloppy contract, not as
a forced exact clone of Reachy Mini. Official Reachy compatibility remains useful
as an optional track when the mechanical and motor choices match upstream
assumptions.

## Research Basis

The Reachy Mini project currently provides enough public material to use it as
the design reference:

- software repo: `https://github.com/pollen-robotics/reachy_mini`
- motor controller repo:
  `https://github.com/pollen-robotics/reachy-mini-motor-controller`
- official docs: `https://huggingface.co/docs/reachy_mini`
- public blog: `https://huggingface.co/blog/reachy-mini`
- ROS docs: `https://docs.ros.org/` and `https://www.ros.org/`
- URDF/MJCF meshes, kinematics data, daemon, FastAPI routers, Python SDK, JS
  SDK, media pipeline, motor setup tools, and MuJoCo simulation are checked into
  the upstream repo.

Important upstream facts:

- Reachy Mini uses a daemon/server architecture. The daemon owns hardware I/O,
  exposes REST under `/api`, exposes SDK WebSocket traffic at `/ws/sdk`, and
  broadcasts joint/head/IMU/status state.
- The SDK talks to the daemon. AI code can run away from the hardware, as long
  as it can reach the daemon.
- The body model has 9 active motors: body yaw, 6 Stewart platform motors, and
  2 antenna motors.
- The canonical motor IDs are `10` for `body_rotation`, `11` through `16` for
  `stewart_1` through `stewart_6`, `17` for `right_antenna`, and `18` for
  `left_antenna`.
- The motor bus runs at `1_000_000` baud and is handled by a Rust
  `reachy_mini_motor_controller` Python binding.
- The hardware docs name 6 `XL330-M288-T` Stewart motors, 2 `XL330-M077-T`
  antenna motors, and a custom base Dynamixel `XC330-M288-PG`.
- The public hardware assets include 86 top-level URDF STL files and 17 files
  named `*_3dprint.stl`.
- Reachy Mini software is Apache 2.0. Hardware design files are documented as
  Creative Commons BY-SA-NC, so any physical derivative must keep that license
  boundary in mind.
- ROS 2 is the right internal robotics substrate for a from-scratch body, but
  not the right direct agent-facing abstraction. The Sloppy-facing boundary
  should remain a curated SLOP provider.

## Recommended Strategy

Use Reachy Mini as the reference body language and API model, but build an
independent Sloppy body contract first.

There are two viable tracks:

- **Track A: official-compatible Dynamixel body.** Reuse the Reachy daemon and
  kinematics by matching the official 9-motor layout, IDs, limits, geometry, and
  bus behavior. This gives maximum software reuse, but depends on expensive
  motors, exact mechanical tolerances, and a replacement for the official custom
  controller and power boards.
- **Track B: Sloppy-Tron body.** Build a simpler Pi 5 robot that
  exposes equivalent high-level affordances to Sloppy, even if the motor layout
  differs. This gets moving immediately and avoids coupling v0 to the full
  Stewart platform.

Track B is the recommended starting point. The external Sloppy contract should
be stable enough that Track A can replace the backend later.

## Body Versions

### v0: Body Dev Rig

Purpose: prove Sloppy can inhabit a physical local body.

Default build: a two-servo pan/tilt head with camera, microphone, speaker, and
visible safety/privacy state.

Hardware:

- Raspberry Pi 5
- two servos for pan and tilt
- small 3D-printed pan/tilt bracket or simple printed head frame
- dedicated servo controller or microcontroller bridge, not direct Pi GPIO PWM
- dedicated servo power rail with shared ground to the controller
- wide-angle camera mounted in the moving head
- USB microphone or small mic array
- speaker or small amplifier board
- visible mute/listening indicator
- optional single status LED or small display
- dedicated motor power rail
- physical power switch and reachable motor cutoff

Behavior:

- wake and sleep
- look left/right/up/down
- look toward a sound direction when available
- nod, shake, curious tilt, idle breathing
- speak and play short sounds
- capture a frame on explicit affordance
- expose safety and privacy state continuously

ROS 2 nodes:

- fake body state publisher
- servo bridge node
- camera state node
- audio state node
- gesture action server
- safety watchdog node
- SLOP adapter node

v0 non-goals:

- no Reachy shell requirement
- no 6-DOF Stewart platform
- no body yaw
- no battery operation
- no arms, wheels, or manipulation
- no remote cloud signaling by default
- no direct arbitrary ROS topic exposure to Sloppy

v0 success criteria:

- Sloppy can observe body connection, pose, media, and safety state.
- Sloppy can wake the body, look left/right/up/down, nod, idle, and sleep.
- Sloppy can speak or play a short sound through the body speaker.
- Sloppy can request a camera frame only through an explicit affordance.
- Motion clamps to configured limits and stops on watchdog or cutoff.
- The fake backend and two-servo backend expose the same SLOP state and
  affordance names.

### v1: Reachy-Shell Custom Body

Purpose: use the upstream printable assets for a recognizable Reachy-like
presence while keeping simpler motion internally.

Candidate top-level printable assets from upstream URDF:

- `antenna_body_3dprint.stl`
- `antenna_holder_l_3dprint.stl`
- `antenna_holder_r_3dprint.stl`
- `antenna_interface_3dprint.stl`
- `body_down_3dprint.stl`
- `body_foot_3dprint.stl`
- `body_top_3dprint.stl`
- `body_turning_3dprint.stl`
- `glasses_dolder_3dprint.stl`
- `head_back_3dprint.stl`
- `head_front_3dprint.stl`
- `head_mic_3dprint.stl`
- `lens_cap_d30_3dprint.stl`
- `lens_cap_d40_3dprint.stl`
- `neck_reference_3dprint.stl`
- `stewart_main_plate_3dprint.stl`
- `stewart_tricap_3dprint.stl`

The upstream asset folder also contains many non-printable or reference meshes:
motors, lenses, bearings, screws, rods, connectors, collision meshes, and CAD
source-like `.part` files. The print set must be manually classified before
ordering hardware around it.

### v2: Stewart Platform Body

Purpose: approach the official Reachy Mini motion envelope.

This version should only start after v0 or v1 proves:

- Sloppy's body affordances feel right in practice
- the power system is stable
- motion safety policy is boring and reliable
- the motor bus choice is settled
- camera, audio, and speech workflows are stable

v2 may use the official motor layout or a compatible equivalent, but if it
diverges mechanically then it should use custom kinematics instead of pretending
to be an official Reachy Mini.

## Hardware Requirements

### Compute

Use Raspberry Pi 5 as the local body computer. It can run:

- body daemon
- camera/audio services
- motor bridge or microcontroller bridge
- optional local wake-word, STT, TTS, and vision models
- Sloppy itself, if desired, or only a body provider reachable from a stronger
  workstation

### Motion

Recommended v0 choices:

- 2-DOF or 3-DOF head with known mechanical limits
- optional 1-DOF body yaw later
- optional expressive antennas
- closed-loop smart servos where practical

Avoid uninstrumented high-torque motion near the head shell. If cheap hobby
servos are used for v0, expose conservative limits, low speed defaults, and
calibration state clearly. If Dynamixels are used, prefer keeping the official
motor names and units where possible.

Official-compatible motor map:

| Function | Upstream name | ID |
| --- | --- | --- |
| Body yaw | `body_rotation` | `10` |
| Stewart branch 1 | `stewart_1` | `11` |
| Stewart branch 2 | `stewart_2` | `12` |
| Stewart branch 3 | `stewart_3` | `13` |
| Stewart branch 4 | `stewart_4` | `14` |
| Stewart branch 5 | `stewart_5` | `15` |
| Stewart branch 6 | `stewart_6` | `16` |
| Right antenna | `right_antenna` | `17` |
| Left antenna | `left_antenna` | `18` |

### Media

Baseline:

- wide-angle Pi camera or USB camera
- USB mic array or ReSpeaker-style mic array
- 5W-class speaker plus amplifier or USB speaker
- hardware mute switch or obvious software mute state

Reachy Mini's daemon uses GStreamer and can release or acquire camera/audio
hardware for direct access. Our body daemon should keep the same concept:
either it owns media and streams frames, or it releases media for direct local
vision/audio pipelines. That state must be observable.

### Power And Safety

Required from the first moving prototype:

- separate logic and motor power planning
- current budget per rail
- fuse or resettable protection where practical
- hard motor cutoff reachable without software
- software emergency stop affordance
- watchdog that disables motion on daemon disconnect
- conservative boot posture
- conservative shutdown posture
- thermal and undervoltage reporting in state when available

## Sloppy Integration Architecture

The body can plug into Sloppy through two complementary paths.

### Path 1: Body As A SLOP Provider

The first integration path is a body provider consumed by an ordinary Sloppy
session:

```text
Sloppy session
  |
  v
sloppy-body SLOP provider
  |
  v
ROS 2 body graph on Pi 5
  |
  +-- motor backend
  +-- camera backend
  +-- microphone backend
  +-- speaker backend
  +-- safety watchdog
```

This is the MVP path. The robot body appears like any other provider: Sloppy
observes `/pose`, `/media`, `/audio`, `/vision`, `/expression`, and `/safety`,
then invokes contextual affordances such as `wake`, `sleep`, `gesture`,
`look_at_point`, `speak`, or `capture_frame`.

Use this path for:

- first implementation
- provider tests with a fake backend
- safety and privacy gating
- direct body control during a conversation
- swapping a custom Pi body and official Reachy Mini daemon behind the same
  Sloppy-facing contract

### Path 2: Body As A Local Sloppy Instance

The second integration path is a body-local Sloppy session running on the Pi 5,
using remote inference when the Pi should not host the model itself:

```text
main Sloppy session
  |
  |  session provider, a2a, messaging, or future Sloppy bridge
  v
body-local Sloppy session on Pi 5
  |
  v
body SLOP provider
  |
  v
ROS 2 body graph on Pi 5
```

The body-local Sloppy instance is not the hardware boundary. It is a resident
agent that consumes the same `body` provider and owns embodiment policy over
time: idle behavior, attention habits, local rituals, quick reactions, and
fallback behavior when the main session is busy or offline.

Use this path for:

- autonomous local presence
- low-latency body routines that should not depend on the main session
- multiple Sloppy instances interacting with one physical body
- long-running "stay alive" behavior such as sleep/wake, idle posture, local
  alerts, and watchdog-friendly responsiveness
- giving the body its own scoped instructions and memory without hiding motors,
  camera, or microphone inside the agent loop

### Sloppy Phase Order

Phase 1:

```text
main Sloppy session
  -> consumes body SLOP provider backed by fake or real body stack
```

Phase 2:

```text
body-local Sloppy session
  -> consumes the same body SLOP provider
  -> uses remote inference profile if needed
  -> owns idle behavior and embodiment routines
```

Phase 3:

```text
main Sloppy session
  <-> body-local Sloppy session
        -> body SLOP provider
```

In Phase 3, the main Sloppy instance handles deeper reasoning, user goals,
workspace context, and cross-device memory. The body-local Sloppy instance
handles physical presence, local timing, and embodied behavior. The physical
body still remains inspectable as provider state.

### Architectural Rule

The hardware must always stay behind a SLOP provider, even when a body-local
Sloppy instance exists.

Do not bury motor, camera, microphone, or speaker controls directly inside a
Sloppy loop. The body provider is the safety, privacy, testing, and observability
boundary. A Sloppy instance may decide how to behave, but the provider owns what
the body can currently sense or do.

This keeps the body:

- inspectable by UIs and other agents
- replaceable with a fake backend or official Reachy backend
- testable without hardware
- safe to share across multiple sessions
- aligned with Sloppy's state-first provider architecture

## ROS 2 Body Stack

Because this project starts from scratch, the first real body implementation
should use ROS 2 internally and expose a SLOP adapter externally:

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
  +-- joint state and transform publishers
  +-- motor driver or ros2_control hardware interface
  +-- camera and audio nodes
  +-- gesture/action server
  +-- calibration services
  +-- safety watchdog and emergency stop nodes
```

ROS 2 should own robotics concerns:

- robot description, transforms, and joint state
- motor-driver isolation
- sensor topics
- lifecycle and health checks
- calibration services
- action servers for gestures and longer movements
- logs, bags, and visualization/debugging through RViz or Foxglove-compatible
  tooling

The SLOP adapter should own agent-facing translation:

- summarize many ROS topics into stable `/pose`, `/media`, `/audio`,
  `/vision`, `/expression`, `/safety`, `/tasks`, and `/calibration` state
- expose semantic affordances rather than raw ROS graph operations
- clamp and validate requests before publishing ROS commands
- hide noisy topic-level details unless the model focuses or asks for
  diagnostics
- mark raw motor commands, calibration, firmware update, and emergency-stop
  reset as guarded or dangerous

Sloppy should not consume arbitrary ROS topics directly. Direct ROS exposure
would recreate a flat tool/topic catalog and push low-level robotics decisions
into the model. The SLOP adapter is the semantic and safety boundary.

Initial platform baseline:

- Raspberry Pi 5
- Ubuntu 24.04
- ROS 2 Jazzy LTS

As of May 8, 2026, Jazzy is the conservative baseline for this project because
it targets Ubuntu 24.04 and has long-term support. Reevaluate newer ROS 2 LTS
releases after they are actually released and Pi, driver, `ros2_control`, and
media support are validated for this body.

### ROS 2 Phase Order

Phase 0: fake ROS body graph.

- publish fake joint, pose, media, safety, and task state
- implement fake gesture action server
- build the SLOP adapter against fake ROS state before hardware exists

Phase 1: ROS 2 body graph plus SLOP adapter.

- run the graph on the Pi 5
- expose a `body` SLOP provider from ROS state
- drive camera, mic, speaker, fake motion, or a single actuator
- verify wake, sleep, look, gesture, and privacy state from Sloppy

Phase 2: real motion backend.

- add 2-DOF or 3-DOF head motion
- add calibration services and persisted limits
- add watchdog and emergency-stop behavior
- graduate from direct driver code to `ros2_control` if the actuator choice
  warrants it

Phase 3: body-local Sloppy.

- run a Pi-local Sloppy session that consumes the same `body` SLOP provider
- use remote inference if needed
- let this session own idle presence, local rituals, and quick reactions

Phase 4: peer Sloppy instances.

- connect main Sloppy and body-local Sloppy through session provider, `a2a`,
  messaging, or a future Sloppy-to-Sloppy bridge
- keep all physical capability observable through the `body` provider

## Body Software Architecture

The body daemon can be a ROS 2 graph plus adapter services rather than a single
custom process. Non-ROS helper processes are still acceptable for media, speech,
or microcontroller bridges when they expose clean ROS nodes or adapter APIs.

The stack should support a fake backend from day one so Sloppy provider tests do
not require hardware.

## SLOP State Surface

Proposed provider id: `body`.

State tree:

```text
/connection
  status
  host
  daemonVersion
  backend
  lastSeenAt
  errors
/body
  name
  model
  coordinateFrame
  capabilities
/pose
  head
  bodyYaw
  antennas
  target
  limits
  moving
/motors
  mode
  bus
  devices
  faults
  temperatures
  voltage
/media
  camera
  microphone
  speaker
  owner
  released
  muted
/audio
  directionOfArrival
  speechDetected
  inputLevel
  outputLevel
/vision
  frameAvailable
  lastFrameSummary
  privacyMode
/expression
  current
  availableGestures
  idleMode
/safety
  motionEnabled
  eStop
  watchdog
  maxSpeed
  maxAmplitude
  privacy
/tasks
  <taskId>
/calibration
  status
  centers
  limits
  requiredSteps
/runtime
  uptime
  logsSummary
  config
```

The model should see whether motion, camera, mic, and speaker are currently
allowed before it sees the corresponding affordances.

## Affordances

Read-only or idempotent:

- `refresh`
- `capture_state_snapshot`
- `get_camera_frame`
- `list_gestures`
- `scan_motors`
- `play_test_sound`

Safe mutating:

- `wake`
- `sleep`
- `look_at_angles`
- `look_at_point`
- `look_toward_sound`
- `gesture`
- `set_idle_mode`
- `set_expression`
- `set_volume`
- `set_microphone_gain`
- `release_media`
- `acquire_media`

Guarded or dangerous:

- `set_motor_mode`
- `enable_motion`
- `disable_motion`
- `calibrate_center`
- `calibrate_limits`
- `raw_motor_command`
- `update_body_firmware`
- `emergency_stop_reset`

Long-running motion affordances should return `accepted` with a task id. Task
state should expose progress, target, started time, cancel affordance, and final
result.

## High-Level Body Contract

Sloppy should issue semantic actions, not raw joint twitches, during normal
conversation:

```ts
type BodyGesture =
  | "nod"
  | "shake_no"
  | "curious_tilt"
  | "look_away"
  | "look_back"
  | "wake"
  | "sleep"
  | "idle_breathe"
  | "small_ack";
```

The provider may translate these differently per backend:

- Reachy Mini daemon backend: call `/api/move/goto`, `/api/move/play/*`, or
  WebSocket commands.
- Custom Pi body backend: call ROS 2 actions, services, and topics backed by
  servo or motor-controller routines.
- Fake backend: update state and task progress only.

This keeps personality timing and body behavior stable while hardware changes.

## Compatibility With Reachy Mini

The official daemon is worth supporting as a backend, but not as the only
target.

Reachy-compatible backend requirements:

- daemon reachable at `http://<host>:8000`
- `/api/daemon/status`
- `/api/state/full`
- `/api/state/ws/full`
- `/api/move/goto`
- `/api/move/set_target`
- `/api/move/play/wake_up`
- `/api/move/play/goto_sleep`
- `/api/move/ws/updates`
- `/api/motors/status`
- `/api/motors/set_mode/{mode}`
- `/api/media/status`
- `/api/media/play_sound`
- `/api/media/release`
- `/api/media/acquire`
- `/ws/sdk` for lower-latency state and commands

If our hardware does not match the official 9-motor geometry, do not run it as
a fake Reachy Mini daemon unless the API clearly reports a custom model. A
custom backend behind the same Sloppy body provider is safer.

## Privacy Policy

The provider must expose visible privacy state:

- camera available or disabled
- microphone available or muted
- speaker available or muted
- whether media is owned by the body daemon or released to another process
- whether frames/audio are local-only or streamed
- whether any remote access path is enabled

Default posture for a home-local body:

- local network only
- no cloud signaling by default
- no camera capture without visible state and an explicit affordance
- no microphone streaming unless actively listening
- no speaker output during sleep except alarms or explicit wake actions

## Test Plan

Provider tests:

- fake backend exposes the full state tree
- unsafe affordances are marked dangerous or approval-gated
- motion affordances clamp targets to configured limits
- `accepted` task lifecycle is observable
- disconnect moves provider state to degraded mode
- media release/acquire state remains coherent
- ROS 2 adapter maps fake ROS state into stable SLOP state without exposing raw
  topic noise by default
- ROS 2 action feedback maps to SLOP task state with cancellation visible

Hardware bench tests:

- no-load motor sweep within limits
- motor cutoff disables motion immediately
- daemon disconnect triggers watchdog
- undervoltage or overcurrent appears in state
- camera and microphone can be physically or logically muted
- startup and shutdown poses are repeatable

Integration tests:

- Sloppy can observe pose and safety state
- Sloppy can perform wake, look, nod, speak, sleep
- Sloppy cannot issue raw motor commands without explicit approval
- fake backend and real backend expose the same high-level affordance names

## Open Blockers

- Exact hardware BOM for a custom build is not selected.
- Official controller and power boards are not public drop-in Pi 5 designs.
- The base actuator is documented as custom.
- Full Stewart platform tolerances, rods, fasteners, bearings, and calibration
  still need a build-level BOM.
- `_3dprint.stl` files must be inspected in slicer/CAD before assuming print
  orientation, supports, material, tolerances, or screw hardware.
- Official hardware design files are BY-SA-NC; derivative use must respect that.
- The custom body must choose between official-compatible Dynamixels, cheaper
  servos, or a hybrid.
- The exact ROS 2 package set, node graph, and actuator interface are not yet
  selected.
- Local STT/TTS/vision stack is separate from body control and should not be
  hidden inside motion code.

## First Milestone

The first milestone is a non-Stewart body dev rig:

- Pi 5
- camera
- mic and speaker
- two-servo pan/tilt head
- servo controller or microcontroller bridge
- dedicated servo power rail and reachable motor cutoff
- visible listening/mute indicator
- ROS 2 body graph with fake and real motor backends
- SLOP adapter exposing the ROS 2 graph as a `body` provider
- semantic body affordances for wake, sleep, look, gesture, and safety controls

Success means Sloppy can hold a local conversation, look around, gesture, sleep,
wake, and make privacy/motion state obvious without relying on official Reachy
hardware.
