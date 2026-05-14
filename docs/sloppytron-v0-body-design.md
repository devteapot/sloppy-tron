# SloppyTron v0 Body Design

SloppyTron v0 is a Reachy-inspired desktop companion body that uses **Sloppy**, the SLOP protocol mascot, as the visual source of truth.

The goal is not to clone Reachy Mini. Reachy is the ergonomic/mechatronic reference: expressive head motion, approachable desktop scale, camera/microphone/speaker placement, and a clean ROS/SLOP body contract. Sloppy is the character reference: blue rounded silhouette, cat-like ears, large glowing green eyes, black eyelids/pupils/nose, and darker side fins.

Source mascot reference:

```text
~/dev/slop/logo/sloppy.svg
```

## Design Lock

Decision: **Reachy-inspired companion, Sloppy-mascot exterior.**

This means:

- Keep the approachable, small desktop robot feel.
- Keep the SLOP-visible body contract stable: `/body`, `/pose`, `/safety`, `/tasks`.
- Preserve the existing semantic joints:
  - `body_yaw_joint`
  - `head_pan_joint`
  - `head_tilt_joint`
  - `antenna_left_joint`
  - `antenna_right_joint`
- Treat the mascot ears as the physical/visual realization of the existing `antenna_*` contract fields.
- Use the mascot face as the robot's identity: two large glowing green eyes, black eye rings, small black nose.
- Avoid derivative Reachy shell geometry. Copy the idea of an expressive companion, not the exact industrial design.

## Visual DNA from `sloppy.svg`

| Mascot element | SVG id / cue | SloppyTron v0 interpretation |
| --- | --- | --- |
| Rounded blue body | `body`, `#4A8FE7` | Main head/body shell color. Rounded organic pod, not hard-edged enclosure. |
| Darker side arms | `left-arm`, `right-arm`, `#2B80CF` | Fixed side fins on v0; possible future expressive arms. |
| Cat-like ears | `left-ear`, `right-ear`, `#4A8FE7` | Servo-addressable ears mapped to `antenna_left/right`. |
| Big green eyes | `left-sclera`, `right-sclera`, `#98F5A6` | Eye lenses / LED diffusers; can double as status display. |
| Black eye rings | `left-eyelid`, `right-eyelid` | Physical black bezels around the eyes. |
| Black pupils | `left-pupil`, `right-pupil` | Static lens detail or animated display target. |
| Small black nose | `nose` | Decorative nose below camera/eyes; can hide status sensor or mic hole if useful. |

Palette:

```text
SLOP blue:       #4A8FE7
SLOP dark blue:  #2B80CF
SLOP eye green:  #98F5A6
Feature black:   #000000
Shell white/gray optional only for internal brackets, not exterior identity.
```

## Mechanical Scope

### v0A — immediate printable/simulated body

v0A is the first custom model and stays intentionally small:

- 2-DOF physical pan/tilt head target.
- Fixed tabletop base.
- Ears/fins visible in the model; ear actuation can be simulated first.
- Camera, mic array, and speaker represented as physical mounting volumes.
- No real motors connected until task lifecycle and safety semantics are locked.

Physical actuation target:

```text
required: head pan, head tilt
simulated/deferred: body yaw, left ear, right ear
fixed/decorative: side fins, nose, face bezels
```

### v0B — first hardware body

Once the safety contract is enforced:

- XL330 pan/tilt servos.
- Read-only motor probe first.
- Then guarded motion enable.
- Optional small ear servos only after head motion is stable.

### v1 — fuller companion

- Base yaw or rotating pedestal.
- Actuated ears.
- Better internal cable path.
- Integrated speaker grille and mic acoustic openings.
- More refined CAD surfaces.

## Coordinate and Joint Convention

ROS coordinate convention for the v0 description:

```text
x: forward from robot face
 y: robot left
 z: up
```

Kinematic tree:

```text
base_link
  -> body_yaw_joint
    -> torso_link
      -> neck_link
        -> head_pan_joint
          -> pan_link
            -> head_tilt_joint
              -> head_link
                -> camera_link
                -> mic_array_link
                -> speaker_link
                -> eye_left/right links
                -> nose_link
                -> antenna_left_joint
                  -> antenna_left_link
                -> antenna_right_joint
                  -> antenna_right_link
                -> left/right fixed side fins
```

The ROS description package is visual/kinematic. The SLOP provider remains the semantic boundary. Raw ROS topics and raw motor controls are not exposed directly to Sloppy.

## First Model Dimensions

These are deliberately approximate for simulation and printable iteration:

| Part | Target dimensions |
| --- | --- |
| Overall height | ~220 mm |
| Head shell | ~150 mm wide, ~120 mm deep, ~130 mm tall |
| Torso/base pod | ~130 mm wide, ~110 mm deep, ~95 mm tall |
| Eye lenses | ~42 mm diameter each |
| Eye spacing | ~70 mm center-to-center |
| Ear height | ~55 mm visible triangle/fin |
| Base footprint | ~130 mm diameter |

Design bias: cute, round, readable from across a desk. The face matters more than exact mechanical realism in v0A.

## ROS Description Assets

Initial package:

```text
ros/src/sloppy_tron_description/
  package.xml
  setup.py
  setup.cfg
  resource/sloppy_tron_description
  sloppy_tron_description/__init__.py
  urdf/sloppy_tron_v0.urdf.xacro
  config/joints.yaml
  meshes/visual/*.stl
  launch/view_sloppy_tron_v0.launch.py
```

The first meshes are intentionally low-poly generated reference shapes. They establish proportions, colors, links, and joint placement. They are not the final printable CAD.

## CAD Direction

Create printable CAD from the ROS description, not the other way around:

1. Lock silhouette and link placements in URDF/RViz.
2. Export simple visual meshes as proportion references.
3. Model printable shell parts in CAD around real component volumes.
4. Keep visual shell separable from structural brackets.
5. Add holes only when actual camera/mic/speaker parts are chosen.

The physical shell should be original SloppyTron artwork. Reachy Mini remains a kinematic/UX reference and simulation oracle, not the source for copied external geometry.

## Acceptance Criteria

A SloppyTron v0 body design pass is acceptable when:

- The model visibly reads as Sloppy: blue rounded body, green eyes, black rings/pupils/nose, cat-like ears.
- The model still maps to the SLOP body contract and existing ROS baseline joint names.
- The model can be loaded as a ROS package without changing the provider/bridge code.
- The design doc clearly separates immediate physical scope from simulated/deferred motion.
- No real motor actuation is required to validate the design.
