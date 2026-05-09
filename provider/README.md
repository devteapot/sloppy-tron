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

`python -m sloppy_tron.provider` defaults to `serve-stdio`, so the example
Sloppy provider config can launch it as a subprocess provider.
