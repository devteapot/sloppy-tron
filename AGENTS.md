# AGENTS.md

## Project

SloppyTron is a local robot body project for Sloppy.

The design rule is:

- ROS 2 owns robotics internals.
- The SLOP provider owns the Sloppy-facing semantic and safety boundary.
- Sloppy consumes the body provider; it does not consume arbitrary ROS topics
  directly.

## Current Sources Of Truth

- `README.md` for the project overview.
- `docs/spec.md` for the current full specification.
- `bom/README.md` for selected components and power notes.
- `ros/README.md` for ROS 2 package layout and node graph notes.
- `provider/README.md` for the SLOP adapter shape.

## Runtime And Package Manager

- Python 3.12 is the on-body runtime. ROS nodes use `rclpy`. ROS packages use
  `ament_python` and are built with `colcon`.
- Use `uv` for non-ROS Python tooling and project-level scripts.
- Do not introduce `npm`, `pnpm`, `yarn`, or `bun` lockfiles. Do not introduce
  `pip-compile`, `conda`, or `pyenv` configs in-tree.
- Target Raspberry Pi 5, Ubuntu 24.04, and ROS 2 Jazzy LTS for the first body.

## Architecture Rules

- Keep physical hardware behind a provider boundary.
- Keep motion safety, privacy state, and emergency controls observable.
- Prefer semantic affordances such as `wake`, `sleep`, `look_at_angles`,
  `gesture`, and `capture_frame` over raw motor controls.
- Mark calibration, raw motor commands, firmware updates, and emergency-stop
  reset as guarded or dangerous.
- Support a fake backend from day one.
- Do not add cloud signaling by default.

## Code Style

- Python code follows PEP 8. 4-space indentation.
- Use `ruff` for both linting and formatting.
- Use explicit type hints at module boundaries; `mypy --strict` for the SLOP
  adapter package.
- Use `object` (or `Any` only when justified) for untrusted input; validate at
  the boundary.
- Prefer named imports (`from x import y`) over star imports.
- Keep comments rare and useful.

## Hardware Safety

- Do not assume direct Pi GPIO PWM is acceptable for servos.
- Use a dedicated servo power rail with shared ground.
- Keep a physical motor cutoff reachable.
- Clamp motion to configured limits before sending commands.
- Watchdog disconnects and degraded state should disable or freeze motion.
- Never hardcode secrets or credentials.
