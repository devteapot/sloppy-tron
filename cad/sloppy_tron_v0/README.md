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

The current Blender pass is **v0.4 corrected SVG / Reachy-body-derived**. It no longer tries to
guess the body from primitives: the body/base/Stewart/speaker geometry is imported from the
upstream Reachy Mini URDF/STL reference, while the head/face/ears are rebuilt from
`~/dev/slop/logo/sloppy.svg`.

Current visual language:

- Reachy Mini body/base/Stewart/speaker geometry reused directly as the mechanical envelope
- Sloppy SVG body path scaled into the head front shell / faceplate
- Sloppy SVG ears mapped upright into antenna-ear shell silhouettes with black mount pucks
- Sloppy SVG arms preserved as visible side arms/flippers on the reused Reachy body
- raised mesh eyes/nose rebuilt from the SVG coordinates for reliable GLB/render readability
- visible six-rod/Stewart-style head-body connector, including front review rods so the linkage is readable in PNG previews
- transparent reservation volumes for Pi Camera Module 3, a Ø65 mm 4-mic array, and a Ø58 mm 5W speaker
- comparison scene with SloppyTron, Reachy Mini, and the source SVG board all front-aligned toward `-Y`; raw Reachy `+X` front is rotated to camera

The reproducible Blender generator is committed at:

```text
cad/sloppy_tron_v0/scripts/build_svg_adapted_reachy_scene.py
```

Run it from repo root with:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --python cad/sloppy_tron_v0/scripts/build_svg_adapted_reachy_scene.py
```

## CAD workflow

1. Open the URDF/meshes in RViz or import the STLs into FreeCAD/Fusion/Blender.
2. Keep the link/joint frame names from the URDF; they match the SLOP body contract.
3. Build printable shells around real component volumes:
   - Pi Camera Module 3 ultrawide
   - ReSpeaker XVF3800 USB mic array
   - small USB speaker
   - XL330 pan/tilt bracket envelope
4. For this v0.4 review pass, reuse Reachy's body geometry as the mechanical starting point and
   make the head/face original from the Sloppy SVG. Before final printable release, audit upstream
   asset licensing and replace any non-redistributable vendor geometry with owned derivatives.
5. Export printable parts into `exports/`; keep editable project/source files in `source/`.

## Reachy reference comparison

`sloppy_tron_v0_reachy_comparison.*` loads the upstream `pollen-robotics/reachy_mini`
`robot_no_collision.urdf` plus Git-LFS STL assets as a neutral gray reference next
to the SloppyTron v0.4 assembly. The comparison scene now rotates Reachy's raw `+X` front to
the camera-facing `-Y` axis for both robots and includes an upright, high-contrast Sloppy SVG
board on the side.

Reference import metrics from the v0.4 comparison pass:

- SloppyTron v0.4 bounding box: `0.210 × 0.163 × 0.316 m`
- Reachy Mini reference bounding box: `0.156 × 0.155 × 0.391 m`
- Imported Reachy visuals: `161`, non-empty meshes: `161`, missing meshes: `0`

If the Reachy import appears empty, the SDK clone is probably holding Git LFS pointer
files instead of real STL data. Fix it with:

```sh
brew install git-lfs
git lfs install --skip-repo
git -C /tmp/reachy_mini lfs pull
```

Next visual pass should refine the now-reference-derived assembly rather than restart from primitives:
turn the obvious front review rods into physically plausible rod brackets, soften the SVG arm/body
attachment, thicken the flat SVG ear shells into printable antenna housings, and turn the transparent
internal reservations into actual bracket/cable-path geometry.

## Hard constraint

Do not design around real motor actuation until the SLOP task lifecycle and safety contract are locked. v0 CAD can reserve brackets, cable paths, and service access; it should not assume live motors are safe yet.
