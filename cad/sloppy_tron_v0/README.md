# SloppyTron v0 CAD Workspace

This directory is for the first custom SloppyTron printable shell.

Visual direction: Reachy-inspired desktop companion, using the Sloppy mascot from
`~/dev/slop/logo/sloppy.svg` as the exterior reference.

## Current status

The committed geometry has two layers:

```text
# ROS visual/kinematic scaffold, not final printable CAD.
ros/src/sloppy_tron_description/urdf/sloppy_tron_v0.urdf.xacro
ros/src/sloppy_tron_description/meshes/visual/*.stl

# Blender visual iteration source and review exports.
cad/sloppy_tron_v0/source/sloppy_tron_v0.blend
cad/sloppy_tron_v0/exports/sloppy_tron_v0.glb
cad/sloppy_tron_v0/exports/sloppy_tron_v0_preview.png

# Side-by-side comparison against the upstream Reachy Mini URDF/STL reference.
cad/sloppy_tron_v0/source/sloppy_tron_v0_reachy_comparison.blend
cad/sloppy_tron_v0/exports/sloppy_tron_v0_reachy_comparison.glb
cad/sloppy_tron_v0/exports/sloppy_tron_v0_reachy_comparison_preview.png
cad/sloppy_tron_v0/exports/sloppy_tron_v0_reachy_comparison_metrics.json
```

The first Blender pass establishes proportions and visual language:

- rounded blue torso/head pod
- cat-like blue ears mapped to `antenna_left/right`
- green eyes with black rings/pupils
- black nose/camera/mic/speaker features
- dark-blue side fins inspired by the mascot arms
- graphite neck/joint markers for ROS contract readability

## CAD workflow

1. Open the URDF/meshes in RViz or import the STLs into FreeCAD/Fusion/Blender.
2. Keep the link/joint frame names from the URDF; they match the SLOP body contract.
3. Build printable shells around real component volumes:
   - Pi Camera Module 3 ultrawide
   - ReSpeaker XVF3800 USB mic array
   - small USB speaker
   - XL330 pan/tilt bracket envelope
4. Keep the exterior original. Reachy is the UX/mechatronic reference, not a geometry source.
5. Export printable parts into `exports/`; keep editable project/source files in `source/`.

## Reachy reference comparison

`sloppy_tron_v0_reachy_comparison.*` loads the upstream `pollen-robotics/reachy_mini`
`robot_no_collision.urdf` plus Git-LFS STL assets as a neutral gray reference next
to the blue SloppyTron shell. It is for envelope, UX, and kinematic comparison only.
Do not copy Reachy exterior geometry into SloppyTron.

Reference import metrics from the first comparison pass:

- SloppyTron v0 bounding box: `0.184 × 0.208 × 0.395 m`
- Reachy Mini reference bounding box: `0.155 × 0.156 × 0.391 m`
- Imported Reachy visuals: `161`, missing meshes: `0`

If the Reachy import appears empty, the SDK clone is probably holding Git LFS pointer
files instead of real STL data. Fix it with:

```sh
brew install git-lfs
git lfs install --skip-repo
git -C /tmp/reachy_mini lfs pull
```

Next visual pass should compare against the reference while preserving the mascot
identity: add subtle mechanical seams/service panels, clarify side articulation, and
rebalance the head/body volume without losing the soft blue companion silhouette.

## Hard constraint

Do not design around real motor actuation until the SLOP task lifecycle and safety contract are locked. v0 CAD can reserve brackets, cable paths, and service access; it should not assume live motors are safe yet.
