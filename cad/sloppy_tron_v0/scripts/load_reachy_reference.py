#!/usr/bin/env python3
# ruff: noqa: E501
"""Load the upstream Reachy Mini URDF reference model into a standalone Blender file.

Source: https://github.com/pollen-robotics/reachy_mini

The repo is expected to be cloned at /tmp/reachy_mini. If missing, this script
will clone it shallowly. Output is written to:

    cad/sloppy_tron_v0/source/reachy_mini_reference.blend
    cad/sloppy_tron_v0/exports/reachy_mini_reference_preview.png

Run with Blender:

    /Applications/Blender.app/Contents/MacOS/Blender -b --python \
        cad/sloppy_tron_v0/scripts/load_reachy_reference.py
"""

from __future__ import annotations

import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

REPO_ROOT = Path(__file__).resolve().parents[3]
CAD_DIR = REPO_ROOT / "cad" / "sloppy_tron_v0"
SOURCE_DIR = CAD_DIR / "source"
EXPORT_DIR = CAD_DIR / "exports"

REACHY_REPO = Path("/tmp/reachy_mini")
REACHY_URDF = REACHY_REPO / "src/reachy_mini/descriptions/reachy_mini/urdf/robot_no_collision.urdf"
REACHY_ASSET_DIR = REACHY_URDF.parent / "assets"

OUTPUT_BLEND = SOURCE_DIR / "reachy_mini_reference.blend"
OUTPUT_PREVIEW = EXPORT_DIR / "reachy_mini_reference_preview.png"


RAW_BASE = "https://github.com/pollen-robotics/reachy_mini/raw/main"


def _is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            head = f.read(64)
        return head.startswith(b"version https://git-lfs.github.com/spec/")
    except OSError:
        return False


def ensure_repo() -> None:
    if not REACHY_URDF.exists():
        REACHY_REPO.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/pollen-robotics/reachy_mini", str(REACHY_REPO)],
            check=True,
        )
        if not REACHY_URDF.exists():
            raise RuntimeError(f"URDF not found after clone: {REACHY_URDF}")

    # The repo tracks STLs via git-lfs. If git-lfs isn't installed locally, the
    # working copy contains LFS pointer stubs (~130 bytes). Resolve those by
    # fetching the real binaries from GitHub's raw endpoint, which auto-serves
    # LFS-tracked files.
    pointers = [p for p in REACHY_ASSET_DIR.glob("*.stl") if _is_lfs_pointer(p)]
    if not pointers:
        return
    print(f"[info] resolving {len(pointers)} LFS pointer STLs from GitHub raw...")
    rel_root = REACHY_REPO
    for stl in pointers:
        rel = stl.relative_to(rel_root).as_posix()
        url = f"{RAW_BASE}/{rel}"
        subprocess.run(["curl", "-sL", "-o", str(stl), url], check=True)
        if _is_lfs_pointer(stl):
            raise RuntimeError(f"LFS resolution failed for {stl}")


@dataclass
class VisualSpec:
    link: str
    mesh: Path
    stem: str
    color: tuple[float, float, float, float]
    matrix: Matrix


@dataclass
class ImportStats:
    attempted: int = 0
    imported: int = 0
    missing: list[str] = field(default_factory=list)


def rpy_xyz_matrix(xyz: str | None, rpy: str | None) -> Matrix:
    tx, ty, tz = (float(x) for x in (xyz or "0 0 0").split())
    rr, pp, yy = (float(x) for x in (rpy or "0 0 0").split())
    mat = Matrix.Translation(Vector((tx, ty, tz)))
    mat @= Euler((rr, pp, yy), "XYZ").to_matrix().to_4x4()
    return mat


def parse_urdf_visuals() -> list[VisualSpec]:
    root = ET.parse(REACHY_URDF).getroot()

    link_visuals: dict[str, list[tuple[Path, tuple[float, float, float, float], Matrix]]] = {}
    links: list[str] = []
    for link in root.findall("link"):
        link_name = link.attrib["name"]
        links.append(link_name)
        visuals = []
        for visual in link.findall("visual"):
            origin = visual.find("origin")
            geom = visual.find("geometry")
            if geom is None:
                continue
            mesh = geom.find("mesh")
            if mesh is None:
                continue
            filename = mesh.attrib.get("filename", "")
            if filename.startswith("package://assets/"):
                mesh_path = REACHY_ASSET_DIR / filename.removeprefix("package://assets/")
            else:
                mesh_path = Path(filename)
            mat_el = visual.find("material/color")
            rgba: tuple[float, float, float, float] = (0.72, 0.72, 0.72, 1.0)
            if mat_el is not None and "rgba" in mat_el.attrib:
                vals = [float(x) for x in mat_el.attrib["rgba"].split()]
                if len(vals) == 4:
                    rgba = (vals[0], vals[1], vals[2], vals[3])
            matrix = rpy_xyz_matrix(
                origin.attrib.get("xyz") if origin is not None else None,
                origin.attrib.get("rpy") if origin is not None else None,
            )
            visuals.append((mesh_path, rgba, matrix))
        link_visuals[link_name] = visuals

    children: dict[str, list[tuple[str, Matrix]]] = {link: [] for link in links}
    child_links: set[str] = set()
    for joint in root.findall("joint"):
        parent = joint.find("parent")
        child = joint.find("child")
        origin = joint.find("origin")
        if parent is None or child is None:
            continue
        parent_name = parent.attrib["link"]
        child_name = child.attrib["link"]
        child_links.add(child_name)
        children.setdefault(parent_name, []).append(
            (
                child_name,
                rpy_xyz_matrix(
                    origin.attrib.get("xyz") if origin is not None else None,
                    origin.attrib.get("rpy") if origin is not None else None,
                ),
            )
        )

    roots = [link for link in links if link not in child_links]
    if not roots:
        raise RuntimeError("URDF has no root link")

    world: dict[str, Matrix] = {roots[0]: Matrix.Identity(4)}
    stack = [roots[0]]
    while stack:
        parent = stack.pop()
        for child, joint_matrix in children.get(parent, []):
            world[child] = world[parent] @ joint_matrix
            stack.append(child)

    specs: list[VisualSpec] = []
    for link, visuals in link_visuals.items():
        link_world = world.get(link, Matrix.Identity(4))
        for mesh_path, color, visual_matrix in visuals:
            specs.append(
                VisualSpec(
                    link=link,
                    mesh=mesh_path,
                    stem=mesh_path.stem,
                    color=color,
                    matrix=link_world @ visual_matrix,
                )
            )
    return specs


def import_stl(filepath: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(filepath))
    else:
        bpy.ops.import_mesh.stl(filepath=str(filepath))
    return [obj for obj in bpy.data.objects if obj not in before]


def make_principled_material(name: str, rgba: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.45
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
    mat.diffuse_color = rgba
    return mat


def reset_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)


def setup_world() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = (0.04, 0.045, 0.05, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def add_camera_and_light() -> None:
    cam_data = bpy.data.cameras.new("ReviewCamera")
    cam = bpy.data.objects.new("ReviewCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.45, -0.55, 0.30)
    cam_data.lens = 50
    cam_data.clip_start = 0.01
    cam_data.clip_end = 50.0
    # Aim camera at the body/head center
    target = Vector((0.0, 0.0, 0.13))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    sun_data = bpy.data.lights.new("KeySun", type="SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("KeySun", sun_data)
    sun.location = (0.6, -0.6, 1.2)
    sun.rotation_euler = (math.radians(55.0), 0.0, math.radians(35.0))
    bpy.context.scene.collection.objects.link(sun)

    fill_data = bpy.data.lights.new("FillSun", type="SUN")
    fill_data.energy = 1.2
    fill = bpy.data.objects.new("FillSun", fill_data)
    fill.location = (-0.9, -0.4, 0.7)
    fill.rotation_euler = (math.radians(70.0), 0.0, math.radians(-50.0))
    bpy.context.scene.collection.objects.link(fill)

    # Brighter world background so the reference reads even with bare materials.
    world = bpy.context.scene.world
    if world is not None and world.use_nodes:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs["Strength"].default_value = 1.5


def import_reachy() -> ImportStats:
    col = bpy.data.collections.new("reachy_mini_reference")
    bpy.context.scene.collection.children.link(col)

    body_mat = make_principled_material("reachy_body_grey", (0.72, 0.72, 0.74, 1.0))
    accent_mat = make_principled_material("reachy_accent_dark", (0.18, 0.19, 0.21, 1.0))

    stats = ImportStats()
    for spec in parse_urdf_visuals():
        stats.attempted += 1
        if not spec.mesh.exists():
            stats.missing.append(str(spec.mesh))
            continue
        objs = import_stl(spec.mesh)
        for obj in objs:
            stats.imported += 1
            obj.name = f"reachy__{spec.stem}"
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            col.objects.link(obj)
            obj.matrix_world = spec.matrix
            obj.data.materials.clear()
            stem = spec.stem.lower()
            mat = accent_mat if any(t in stem for t in ("speaker", "bearing", "rod", "horn", "arm", "stewart")) else body_mat
            obj.data.materials.append(mat)
    return stats


def render_preview(path: Path) -> None:
    scene = bpy.context.scene
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    print(f"[info] available engines: {sorted(engines)}")
    for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        if candidate in engines:
            scene.render.engine = candidate
            print(f"[info] using engine: {candidate}")
            break
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> int:
    ensure_repo()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    reset_scene()
    setup_world()
    stats = import_reachy()
    add_camera_and_light()

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    try:
        render_preview(OUTPUT_PREVIEW)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] preview render skipped: {exc}", file=sys.stderr)

    print(f"[done] saved {OUTPUT_BLEND}")
    print(f"[done] imported {stats.imported}/{stats.attempted} visuals")
    if stats.missing:
        print(f"[warn] {len(stats.missing)} missing meshes")
        for m in stats.missing[:10]:
            print(f"  - {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
