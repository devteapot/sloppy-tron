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
