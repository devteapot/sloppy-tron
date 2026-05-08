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
