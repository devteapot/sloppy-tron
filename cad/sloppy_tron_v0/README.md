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

The current Blender pass is **v0.2 productized**: mascot-first, but no longer a primitive blockout.
It keeps the blue Sloppy identity while borrowing Reachy's product logic: stable base, visible
neck/gimbal mechanics, service seams, fastener details, and real sensor/speaker affordances.

Current visual language:

- rounded blue torso/head pod with flatter manufactured faceplate
- slim mascot ears mapped to `antenna_left/right`, with visible black mounts
- green SLOP eyes inside black optical bezels
- black nose/camera/mic/speaker features integrated into the face/body surfaces
- dark-blue side fins as shell panels, not detached arms
- graphite neck, bearing rings, support rods, pivot caps, screws, and gasket seams

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

Reference import metrics from the v0.2 comparison pass:

- SloppyTron v0.2 bounding box: `0.181 × 0.148 × 0.432 m` including antenna ears
- Reachy Mini reference bounding box: `0.155 × 0.156 × 0.391 m`
- Imported Reachy visuals: `161`, non-empty meshes: `161`, missing meshes: `0`

If the Reachy import appears empty, the SDK clone is probably holding Git LFS pointer
files instead of real STL data. Fix it with:

```sh
brew install git-lfs
git lfs install --skip-repo
git -C /tmp/reachy_mini lfs pull
```

Next visual pass should refine the now-productized shell rather than restart from primitives:
soften the debug-looking gasket curves where they feel too graphic, tune the base/body collar,
make the antenna-ear silhouette readable from more angles, and begin reserving real internal
volumes for camera/audio/speaker hardware.

## Hard constraint

Do not design around real motor actuation until the SLOP task lifecycle and safety contract are locked. v0 CAD can reserve brackets, cable paths, and service access; it should not assume live motors are safe yet.
