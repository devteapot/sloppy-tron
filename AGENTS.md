# AGENTS.md

## Project

Sloppy-Tron is a local robot body project for Sloppy.

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

- Use Bun for TypeScript scripts and package management.
- Do not introduce `npm`, `pnpm`, or `yarn` lockfiles.
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

- TypeScript code uses ESM imports/exports.
- Prefer named exports.
- Use explicit types at module boundaries.
- Use `unknown` for untrusted input.
- Keep comments rare and useful.
- Use 2-space indentation and semicolons.

## Hardware Safety

- Do not assume direct Pi GPIO PWM is acceptable for servos.
- Use a dedicated servo power rail with shared ground.
- Keep a physical motor cutoff reachable.
- Clamp motion to configured limits before sending commands.
- Watchdog disconnects and degraded state should disable or freeze motion.
- Never hardcode secrets or credentials.
