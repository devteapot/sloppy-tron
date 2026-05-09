# SLOP Provider

The provider exposes SloppyTron as provider id `body`.

Initial state surface:

- `/connection`
- `/body`
- `/pose`
- `/motors`
- `/media`
- `/audio`
- `/vision`
- `/expression`
- `/safety`
- `/tasks`
- `/calibration`
- `/runtime`

Initial affordances:

- `wake`
- `sleep`
- `look_at_angles`
- `look_at_point`
- `look_toward_sound`
- `gesture`
- `capture_frame`
- `set_idle_mode`
- `enable_motion`
- `disable_motion`
- `emergency_stop`

The adapter should map ROS 2 state/actions into this semantic SLOP surface.

The provider exposes `/body` as the spec-aligned identity node. There is no
`/identity` compatibility alias while the contract is still actively evolving.

`src/sloppy_tron/provider/contract.py` explicitly partitions declared
affordances into `IMPLEMENTED_AFFORDANCE_NAMES` and `FUTURE_AFFORDANCE_NAMES`.
Tests verify the implemented set is actually exposed across representative body
states, while future low-level/calibration controls remain declared but hidden.

Safety semantics: `wake` is a high-level safe posture transition that may enable
only conservative clamped body behavior in the current fake/v0 contract.
`enable_motion` remains a guarded control for arming lower-level/manual motion
paths and should stay approval-gated before real hardware is attached.

## Current Python Scaffold

The initial fake provider contract lives in `src/sloppy_tron/provider` and uses
the PyPI `slop-ai` SDK for SLOP node descriptors, affordances, validation, and
stdio/unix transports.

Useful local commands:

```sh
uv run python -m sloppy_tron.provider serve-stdio
uv run python -m sloppy_tron.provider serve-unix --register
uv run python -m sloppy_tron.provider tree
uv run python -m sloppy_tron.provider snapshot
uv run python -m sloppy_tron.provider wake
uv run python -m sloppy_tron.provider look-at-angles --pan 30 --tilt -10
```

The fake backend is intentionally hardware-free. It exposes the state tree,
marks risky controls as guarded or dangerous, clamps look targets to configured
limits, and records observable task state for accepted actions.

A Reachy Mini daemon backend is also available behind the same consumer-facing
SLOP contract. It talks to the upstream daemon over FastAPI, so the consumer sees
`/body`, `/pose`, `/safety`, `/tasks`, etc. regardless of whether the body behind
that boundary is fake, ROS 2, mockup-sim, MuJoCo, or later real hardware:

```sh
# Terminal 1: upstream Reachy Mini daemon, MuJoCo/headless
reachy-mini-daemon \
  --sim \
  --headless \
  --scene empty \
  --no-media \
  --no-wake-up-on-start \
  --no-goto-sleep-on-stop \
  --fastapi-port 8001

# Terminal 2: expose the same SLOP provider contract backed by that daemon
uv run python -m sloppy_tron.provider \
  --backend reachy \
  --reachy-host localhost \
  --reachy-port 8001 \
  snapshot

uv run python -m sloppy_tron.provider \
  --backend reachy \
  --reachy-port 8001 \
  serve-stdio
```

For a local smoke test when `reachy-mini-daemon` is installed with the MuJoCo
extra, run:

```sh
./docker/reachy-mujoco-smoke.sh mujoco
# or the lighter no-physics upstream backend:
./docker/reachy-mujoco-smoke.sh mockup
```

The smoke client verifies daemon status, enables motion, sends a semantic
`look_at_angles` command through `ReachyDaemonBackend`, and checks that the final
state still has the standard SLOP body-provider shape.

`python -m sloppy_tron.provider` defaults to `serve-stdio`, so the example
Sloppy provider config can launch it as a subprocess provider.
