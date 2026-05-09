#!/usr/bin/env python3
# ruff: noqa: E501
"""Build the SloppyTron v0.3 SVG-adapted Reachy-derived review assets.

This script intentionally uses the upstream Reachy Mini URDF/STL geometry as the
body/mechanics starting point, then replaces the head/face with geometry derived
from the Sloppy mascot SVG. It also places the source SVG in-scene as a side
reference so geometry and mascot silhouette can be compared directly.

Run with Blender, not CPython:

    /Applications/Blender.app/Contents/MacOS/Blender -b --python cad/sloppy_tron_v0/scripts/build_svg_adapted_reachy_scene.py
"""

from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

REPO_ROOT = Path(__file__).resolve().parents[3]
CAD_DIR = REPO_ROOT / "cad" / "sloppy_tron_v0"
SOURCE_DIR = CAD_DIR / "source"
EXPORT_DIR = CAD_DIR / "exports"
REACHY_URDF = Path(
    "/tmp/reachy_mini/src/reachy_mini/descriptions/reachy_mini/urdf/robot_no_collision.urdf"
)
REACHY_ASSET_DIR = REACHY_URDF.parent / "assets"
SLOPPY_SVG = Path("/Users/sloppy/dev/slop/logo/sloppy.svg")

PRIMARY_BLEND = SOURCE_DIR / "sloppy_tron_v0.blend"
PRIMARY_GLB = EXPORT_DIR / "sloppy_tron_v0.glb"
PRIMARY_PREVIEW = EXPORT_DIR / "sloppy_tron_v0_preview.png"
COMPARISON_BLEND = SOURCE_DIR / "sloppy_tron_v0_reachy_comparison.blend"
COMPARISON_GLB = EXPORT_DIR / "sloppy_tron_v0_reachy_comparison.glb"
COMPARISON_PREVIEW = EXPORT_DIR / "sloppy_tron_v0_reachy_comparison_preview.png"
COMPARISON_METRICS = EXPORT_DIR / "sloppy_tron_v0_reachy_comparison_metrics.json"

# Sloppy palette from ~/dev/slop/logo/sloppy.svg
SLOP_BLUE = (0x4A / 255.0, 0x8F / 255.0, 0xE7 / 255.0, 1.0)
SLOP_DARK_BLUE = (0x2B / 255.0, 0x80 / 255.0, 0xCF / 255.0, 1.0)
EYE_GREEN = (0x98 / 255.0, 0xF5 / 255.0, 0xA6 / 255.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)
GRAPHITE = (0.07, 0.08, 0.09, 1.0)
DARK_GRAPHITE = (0.015, 0.017, 0.02, 1.0)
REF_GREY = (0.55, 0.58, 0.60, 0.72)
REF_DARK = (0.26, 0.28, 0.30, 0.72)
WARM_WHITE = (0.86, 0.90, 0.92, 1.0)
BOARD = (0.035, 0.042, 0.052, 0.72)
CYAN_GLASS = (0.1, 0.9, 1.0, 0.28)
AMBER_GLASS = (1.0, 0.58, 0.15, 0.26)
PURPLE_GLASS = (0.70, 0.28, 1.0, 0.24)

HEAD_REPLACEMENT_STEMS = {
    "head_front_3dprint",
    "head_back_3dprint",
    "head_mic_3dprint",
    "head_head_back",
    "head_shell_front",
    "pp01069_head_shell_front",
    "pp01070_head_head_back",
    "pp01078_glasses",
    "pp01079_back_big_eye",
    "pp01080_back_small_eye",
    "glasses_dolder_3dprint",
    "small_lens",
    "small_lens_d30",
    "big_lens",
    "big_lens_d40",
    "lens_cap_d30_3dprint",
    "lens_cap_d40_3dprint",
    "m12_lens",
    "m12_fisheye_lens_1_8mm",
    "arducam",
    "pp01102_arducam_carter",
    "eye_support",
}

# Keep the reference body/mechanics and speaker. Replace Reachy head and antennas
# with mascot/SVG-derived head, ears, eyes, and nose.
ANTENNA_REPLACEMENT_STEMS = {
    "antenna",
    "antenna_body_3dprint",
    "antenna_holder_l_3dprint",
    "antenna_holder_r_3dprint",
    "antenna_interface_3dprint",
    "test_antenna",
    "test_antenna_body",
}

SVG_MATERIAL_HINTS = {
    "body": "slop_blue",
    "left-ear": "slop_blue",
    "right-ear": "slop_blue",
    "left-arm": "slop_dark_blue",
    "right-arm": "slop_dark_blue",
    "left-sclera": "eye_green",
    "right-scalera": "eye_green",
    "left-glow": "eye_green",
    "right-glow": "eye_green",
    "left-eyelid": "black",
    "right-eyelid": "black",
    "left-pupil": "black",
    "right-pupil": "black",
    "nose": "black",
}


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
    non_empty: int = 0
    missing: list[str] | None = None

    def __post_init__(self) -> None:
        if self.missing is None:
            self.missing = []


@dataclass
class AssemblyResult:
    objects: list[bpy.types.Object]
    stats: ImportStats


def ensure_dirs() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent
    script_dir.mkdir(parents=True, exist_ok=True)


def require_inputs() -> None:
    missing = [p for p in [REACHY_URDF, REACHY_ASSET_DIR, SLOPPY_SVG] if not p.exists()]
    if missing:
        for path in missing:
            print(f"missing required input: {path}", file=sys.stderr)
        raise SystemExit(2)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        if block.users == 0:
            bpy.data.curves.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)


def material(name: str, rgba: tuple[float, float, float, float], *, emission: float = 0.0) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Alpha"].default_value = rgba[3]
        bsdf.inputs["Roughness"].default_value = 0.58
        bsdf.inputs["Metallic"].default_value = 0.0
        if emission > 0:
            # Blender 5 keeps these inputs on the Principled node.
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = rgba
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = rgba
    if rgba[3] < 1.0:
        mat.blend_method = "BLEND"
        mat.use_screen_refraction = True
        mat.show_transparent_back = True
    return mat


def make_materials() -> dict[str, bpy.types.Material]:
    return {
        "slop_blue": material("slop_blue__svg_4A8FE7", SLOP_BLUE, emission=0.12),
        "slop_dark_blue": material("slop_dark_blue__svg_2B80CF", SLOP_DARK_BLUE, emission=0.08),
        "eye_green": material("eye_green__svg_98F5A6", EYE_GREEN, emission=1.25),
        "black": material("black__svg_detail", BLACK),
        "graphite": material("graphite_mechanics", GRAPHITE),
        "dark_graphite": material("dark_graphite_voids", DARK_GRAPHITE),
        "warm_white": material("warm_white_internal", WARM_WHITE),
        "reference_grey": material("transparent_reachy_reference_grey", REF_GREY),
        "reference_dark": material("transparent_reachy_reference_dark", REF_DARK),
        "board": material("dark_reference_board", BOARD),
        "camera_volume": material("reserved_camera_volume_cyan", CYAN_GLASS),
        "audio_volume": material("reserved_audio_volume_amber", AMBER_GLASS),
        "speaker_volume": material("reserved_speaker_volume_purple", PURPLE_GLASS),
    }


def rpy_xyz_matrix(xyz: str | None, rpy: str | None) -> Matrix:
    tx, ty, tz = (float(x) for x in (xyz or "0 0 0").split())
    rr, pp, yy = (float(x) for x in (rpy or "0 0 0").split())
    mat = Matrix.Translation(Vector((tx, ty, tz)))
    # URDF fixed-axis RPY is equivalent to Blender XYZ Euler for these meshes.
    mat @= Euler((rr, pp, yy), "XYZ").to_matrix().to_4x4()
    return mat


def parse_urdf_visuals() -> list[VisualSpec]:
    root = ET.parse(REACHY_URDF).getroot()

    link_visuals: dict[str, list[tuple[Path, tuple[float, float, float, float], Matrix]]] = {}
    links = []
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
            rgba = (0.72, 0.72, 0.72, 1.0)
            if mat_el is not None and "rgba" in mat_el.attrib:
                vals = [float(x) for x in mat_el.attrib["rgba"].split()]
                if len(vals) == 4:
                    rgba = tuple(vals)  # type: ignore[assignment]
            matrix = rpy_xyz_matrix(
                origin.attrib.get("xyz") if origin is not None else None,
                origin.attrib.get("rpy") if origin is not None else None,
            )
            visuals.append((mesh_path, rgba, matrix))
        link_visuals[link_name] = visuals

    children: dict[str, list[tuple[str, Matrix]]] = {link: [] for link in links}
    child_links = set()
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


def make_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)


def import_stl(filepath: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(filepath))
    else:
        bpy.ops.import_mesh.stl(filepath=str(filepath))
    return [obj for obj in bpy.data.objects if obj not in before]


def choose_sloppy_material(stem: str, mats: dict[str, bpy.types.Material]) -> bpy.types.Material:
    lower = stem.lower()
    if "body_top" in lower or "body_down" in lower or lower in {"top_body", "bottom_body", "pp01068_top_body", "pp01067_bottom_body"}:
        return mats["slop_blue"]
    if "foot" in lower or "turning" in lower:
        return mats["slop_dark_blue"]
    if "speaker" in lower:
        return mats["black"]
    if any(token in lower for token in ["bearing", "stewart", "plate", "rod", "horn", "case", "bts", "b3b", "phs"]):
        return mats["graphite"]
    return mats["warm_white"]


def choose_reference_material(stem: str, mats: dict[str, bpy.types.Material]) -> bpy.types.Material:
    lower = stem.lower()
    if any(token in lower for token in ["body", "head", "antenna", "glasses"]):
        return mats["reference_grey"]
    return mats["reference_dark"]


def assign_mat(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def import_reachy_assembly(
    *,
    collection_name: str,
    root_matrix: Matrix,
    mats: dict[str, bpy.types.Material],
    mode: str,
    skip_stems: set[str] | None = None,
) -> AssemblyResult:
    skip_stems = skip_stems or set()
    col = make_collection(collection_name)
    stats = ImportStats()
    imported: list[bpy.types.Object] = []
    for spec in parse_urdf_visuals():
        if spec.stem in skip_stems:
            continue
        stats.attempted += 1
        if not spec.mesh.exists():
            stats.missing.append(str(spec.mesh))
            continue
        objs = import_stl(spec.mesh)
        for obj in objs:
            stats.imported += 1
            obj.name = f"{collection_name}__{spec.stem}"
            move_to_collection(obj, col)
            obj.matrix_world = root_matrix @ spec.matrix
            if mode == "sloppy":
                assign_mat(obj, choose_sloppy_material(spec.stem, mats))
            else:
                assign_mat(obj, choose_reference_material(spec.stem, mats))
            if obj.type == "MESH" and len(obj.data.vertices) > 0:
                stats.non_empty += 1
                try:
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.shade_smooth()
                    obj.select_set(False)
                except Exception:
                    pass
            imported.append(obj)
    return AssemblyResult(objects=imported, stats=stats)


def world_bbox(objects: Iterable[bpy.types.Object]) -> tuple[Vector, Vector]:
    bpy.context.view_layer.update()
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    seen = False
    for obj in objects:
        if obj.type not in {"MESH", "CURVE", "FONT"}:
            continue
        for corner in obj.bound_box:
            pt = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, pt.x)
            mins.y = min(mins.y, pt.y)
            mins.z = min(mins.z, pt.z)
            maxs.x = max(maxs.x, pt.x)
            maxs.y = max(maxs.y, pt.y)
            maxs.z = max(maxs.z, pt.z)
            seen = True
    if not seen:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return mins, maxs


def bbox_dims(objects: Iterable[bpy.types.Object]) -> tuple[float, float, float]:
    mins, maxs = world_bbox(objects)
    dims = maxs - mins
    return (round(float(dims.x), 4), round(float(dims.y), 4), round(float(dims.z), 4))


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera_and_light(*, target: Vector, radius: float, z: float, focal_length: float = 55.0) -> None:
    bpy.ops.object.light_add(type="AREA", location=(0.0, -0.7, 0.68))
    light = bpy.context.object
    light.name = "large_softbox_front"
    light.data.energy = 520
    light.data.size = 0.55

    bpy.ops.object.light_add(type="POINT", location=(-0.45, 0.35, 0.45))
    rim = bpy.context.object
    rim.name = "cool_rim_light"
    rim.data.energy = 90

    bpy.ops.object.camera_add(location=(target.x + 0.02, -radius, z))
    camera = bpy.context.object
    camera.name = "front_review_camera__front_is_negative_y"
    camera.data.lens = focal_length
    camera.data.sensor_width = 32
    look_at(camera, target)
    bpy.context.scene.camera = camera


def add_floor(width: float = 1.0, depth: float = 0.75) -> None:
    mat = material("matte_floor", (0.018, 0.021, 0.026, 1.0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.02, -0.006))
    floor = bpy.context.object
    floor.name = "matte_floor_plane"
    floor.dimensions = (width, depth, 0.006)
    assign_mat(floor, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def add_text(
    text: str,
    *,
    location: tuple[float, float, float],
    size: float = 0.012,
    align: str = "CENTER",
    mat_name: str = "text_light",
) -> bpy.types.Object:
    mat = material(mat_name, (0.86, 0.92, 1.0, 1.0), emission=0.08)
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = "label__" + text[:32].replace(" ", "_").replace("/", "_")
    obj.data.body = text
    obj.data.size = size
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    assign_mat(obj, mat)
    return obj


def import_svg_objects(collection_name: str) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(SLOPPY_SVG))
    new_objs = [obj for obj in bpy.data.objects if obj not in before]
    col = make_collection(collection_name)
    for obj in new_objs:
        move_to_collection(obj, col)
    return new_objs


def transform_svg_to_vertical_plane(
    objs: list[bpy.types.Object],
    *,
    center: tuple[float, float, float],
    height: float,
    z_tilt_deg: float = 0.0,
) -> None:
    mins, maxs = world_bbox(objs)
    src_center = Vector(((mins.x + maxs.x) / 2.0, (mins.y + maxs.y) / 2.0, 0.0))
    src_height = maxs.y - mins.y
    scale = height / src_height
    base = (
        Matrix.Translation(Vector(center))
        @ Matrix.Rotation(math.radians(z_tilt_deg), 4, "Z")
        @ Matrix.Rotation(-math.pi / 2, 4, "X")
        @ Matrix.Scale(scale, 4)
        @ Matrix.Translation(-src_center)
    )
    for obj in objs:
        obj.matrix_world = base @ obj.matrix_world


def set_svg_materials(
    objs: list[bpy.types.Object],
    mats: dict[str, bpy.types.Material],
    *,
    alpha: float | None = None,
) -> None:
    for obj in objs:
        name = obj.name.split(".")[0]
        mat_key = SVG_MATERIAL_HINTS.get(name, "slop_blue")
        mat = mats[mat_key]
        if alpha is not None:
            rgba = tuple(mat.diffuse_color[:3]) + (alpha,)
            mat = material(f"{mat.name}__alpha_{alpha:.2f}", rgba)
        if hasattr(obj.data, "materials"):
            assign_mat(obj, mat)


def keep_only_svg_parts(objs: list[bpy.types.Object], keep: set[str]) -> list[bpy.types.Object]:
    kept: list[bpy.types.Object] = []
    for obj in list(objs):
        base = obj.name.split(".")[0]
        if base in keep:
            kept.append(obj)
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
    return kept


def set_curve_extrusion(objs: list[bpy.types.Object], *, extrude: float, bevel: float) -> None:
    for obj in objs:
        if obj.type == "CURVE":
            obj.data.dimensions = "2D"
            obj.data.fill_mode = "BOTH"
            obj.data.extrude = extrude
            obj.data.bevel_depth = bevel
            obj.data.resolution_u = 18


def create_svg_head(center_x: float, mats: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    """Create an SVG-first mascot head mounted on the Reachy neck/body."""
    objects: list[bpy.types.Object] = []

    # Soft 3D rear volume sized to the Reachy head envelope, with the actual SVG
    # silhouette used as the visible front plate and facial geometry.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=(center_x, -0.004, 0.315))
    rear = bpy.context.object
    rear.name = "sloppy_svg_head__rounded_rear_volume"
    rear.scale = (0.060, 0.044, 0.066)
    assign_mat(rear, mats["slop_blue"])
    bpy.ops.object.shade_smooth()
    objects.append(rear)

    # A shallow black shadow/collar behind the SVG face reduces the flat-card look.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=24, radius=1, location=(center_x, -0.047, 0.315))
    shadow = bpy.context.object
    shadow.name = "sloppy_svg_head__black_recess_behind_faceplate"
    shadow.scale = (0.0615, 0.010, 0.0675)
    assign_mat(shadow, mats["dark_graphite"])
    bpy.ops.object.shade_smooth()
    objects.append(shadow)

    shell = import_svg_objects("svg_head_faceplate_shell")
    shell = keep_only_svg_parts(shell, {"body", "left-ear", "right-ear"})
    transform_svg_to_vertical_plane(shell, center=(center_x, -0.060, 0.316), height=0.146)
    set_svg_materials(shell, mats)
    # Values are pre-scale local units; after SVG scale this produces a raised,
    # manufacturable plate instead of a purely flat sticker.
    set_curve_extrusion(shell, extrude=0.0017, bevel=0.00035)
    for obj in shell:
        obj.name = "sloppy_svg_head_shell__" + obj.name
    objects.extend(shell)

    # Raised mesh details rebuilt from the SVG's actual face coordinates. These
    # stay readable in renders/GLB viewers even when the imported SVG curves are
    # viewed from an oblique angle.
    objects.extend(create_svg_face_mesh_details(center_x, mats))

    # Ear hinge pucks: SVG silhouette supplies the shape; these show how the
    # geometry mounts onto the real Reachy-like head envelope.
    for side, sx in [("left", -0.044), ("right", 0.044)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(center_x + sx, -0.050, 0.377))
        puck = bpy.context.object
        puck.name = f"sloppy_svg_head__{side}_ear_black_mount"
        puck.scale = (0.009, 0.007, 0.009)
        assign_mat(puck, mats["black"])
        bpy.ops.object.shade_smooth()
        objects.append(puck)

    # Simple mechanical adapter from the reused Reachy Stewart platform to the
    # mascot head. This is intentionally visible; it helps compare head envelope
    # against the body instead of hiding the transition.
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.037, depth=0.018, location=(center_x, 0.0, 0.238))
    collar = bpy.context.object
    collar.name = "sloppy_reachy_body_adapter__head_neck_collar"
    assign_mat(collar, mats["graphite"])
    bpy.ops.object.shade_smooth()
    objects.append(collar)

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.052, depth=0.010, location=(center_x, 0.0, 0.219))
    bearing = bpy.context.object
    bearing.name = "sloppy_reachy_body_adapter__upper_bearing_ring"
    assign_mat(bearing, mats["dark_graphite"])
    bpy.ops.object.shade_smooth()
    objects.append(bearing)

    return objects


def add_face_disc(
    *,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=96,
        radius=radius,
        depth=depth,
        rotation=(math.pi / 2, 0, 0),
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    assign_mat(obj, mat)
    bpy.ops.object.shade_smooth()
    return obj


def add_eye_ring(
    *,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=0.0022,
        major_segments=96,
        minor_segments=10,
        rotation=(math.pi / 2, 0, 0),
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    assign_mat(obj, mat)
    bpy.ops.object.shade_smooth()
    return obj


def add_flat_triangle(
    *,
    name: str,
    points_xz: list[tuple[float, float]],
    y: float,
    mat: bpy.types.Material,
) -> bpy.types.Object:
    verts = [(x, y, z) for x, z in points_xz]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    assign_mat(obj, mat)
    return obj


def create_svg_face_mesh_details(center_x: float, mats: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    """Create robust mesh face details from the SVG's actual pixel coordinates.

    The imported SVG curves stay in-scene as reference/silhouette, but the eyes
    and nose are also rebuilt as raised meshes so they remain readable in
    renders, GLB viewers, and from oblique angles.
    """
    objects: list[bpy.types.Object] = []
    scale = 0.146 / 158.0
    svg_center_x = 76.6268
    svg_center_y = 79.0
    front_y = -0.071
    center_z = 0.316

    def map_pt(x: float, y: float) -> tuple[float, float, float]:
        return (center_x + (x - svg_center_x) * scale, front_y, center_z + (svg_center_y - y) * scale)

    left_eye = map_pt(47.1714, 60.0454)
    right_eye = map_pt(106.171, 60.0454)
    left_pupil = map_pt(55.1714, 60.0454)
    right_pupil = map_pt(99.1714, 60.0454)
    eye_radius = 26.5 * scale
    pupil_radius = 9.5 * scale

    for side, loc in [("left", left_eye), ("right", right_eye)]:
        objects.append(
            add_face_disc(
                name=f"sloppy_svg_face_mesh__{side}_green_eye_disc",
                location=loc,
                radius=eye_radius,
                depth=0.0022,
                mat=mats["eye_green"],
            )
        )
        objects.append(
            add_eye_ring(
                name=f"sloppy_svg_face_mesh__{side}_black_eye_ring",
                location=(loc[0], front_y - 0.0016, loc[2]),
                radius=eye_radius,
                mat=mats["black"],
            )
        )

    for side, loc in [("left", left_pupil), ("right", right_pupil)]:
        objects.append(
            add_face_disc(
                name=f"sloppy_svg_face_mesh__{side}_black_pupil",
                location=(loc[0], front_y - 0.0026, loc[2]),
                radius=pupil_radius,
                depth=0.0024,
                mat=mats["black"],
            )
        )

    nose_pts = [map_pt(71.1714, 82.0454), map_pt(76.6714, 73.5454), map_pt(82.1714, 82.0454)]
    objects.append(
        add_flat_triangle(
            name="sloppy_svg_face_mesh__black_triangle_nose_from_svg",
            points_xz=[(p[0], p[2]) for p in nose_pts],
            y=front_y - 0.0035,
            mat=mats["black"],
        )
    )
    return objects


def add_internal_reservation_volumes(center_x: float, mats: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []

    # Raspberry Pi Camera Module 3 board envelope: 25 x 24 x ~11.5 mm.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center_x, -0.036, 0.318))
    cam = bpy.context.object
    cam.name = "reserved_internal_volume__pi_camera_module_3_25x24x12mm"
    cam.dimensions = (0.025, 0.012, 0.024)
    assign_mat(cam, mats["camera_volume"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    objects.append(cam)

    # 4-mic XVF3800-style circular array reservation. This is a placeholder
    # envelope, not a specific vendor PCB lock-in.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=0.0325,
        depth=0.006,
        rotation=(math.pi / 2, 0, 0),
        location=(center_x, -0.038, 0.263),
    )
    mic = bpy.context.object
    mic.name = "reserved_internal_volume__xvf3800_four_mic_array_d65x6mm"
    assign_mat(mic, mats["audio_volume"])
    bpy.ops.object.shade_smooth()
    objects.append(mic)

    # Speaker volume follows the Reachy body's real 5W speaker location; the
    # upstream STL is also present in the reused body import.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=0.029,
        depth=0.018,
        rotation=(math.pi / 2, 0, 0),
        location=(center_x, -0.055, 0.088),
    )
    spk = bpy.context.object
    spk.name = "reserved_internal_volume__5w_speaker_d58x18mm"
    assign_mat(spk, mats["speaker_volume"])
    bpy.ops.object.shade_smooth()
    objects.append(spk)

    label_x = center_x + 0.092
    add_text("camera 25×24×12", location=(label_x, -0.067, 0.352), size=0.0062, mat_name="text_cyan")
    add_text("4-mic array Ø65", location=(label_x, -0.067, 0.238), size=0.0062, mat_name="text_amber")
    add_text("5W speaker Ø58", location=(label_x, -0.067, 0.045), size=0.0062, mat_name="text_purple")

    return objects


def add_svg_reference_board(
    *,
    center: tuple[float, float, float],
    height: float,
    mats: dict[str, bpy.types.Material],
    label: str = "Sloppy SVG",
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    # Board behind the imported SVG curves, in the same front-facing vertical plane.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(center[0], center[1] + 0.004, center[2]))
    board = bpy.context.object
    board.name = "side_loaded_reference_svg__dark_backing_card"
    board.dimensions = (height * 0.82, 0.004, height * 1.10)
    assign_mat(board, mats["board"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    objects.append(board)

    svg_objs = import_svg_objects("side_loaded_reference_svg_curves")
    transform_svg_to_vertical_plane(svg_objs, center=center, height=height)
    set_svg_materials(svg_objs, mats)
    set_curve_extrusion(svg_objs, extrude=0.00025, bevel=0.0)
    for obj in svg_objs:
        obj.name = "side_loaded_reference_svg__" + obj.name
    objects.extend(svg_objs)

    objects.append(add_text(label, location=(center[0], center[1] - 0.012, center[2] - height * 0.62), size=0.0075))
    return objects


def convert_curve_and_text_to_mesh() -> None:
    for obj in list(bpy.context.scene.objects):
        if obj.type in {"CURVE", "FONT"}:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            try:
                bpy.ops.object.convert(target="MESH")
            except Exception as exc:
                print(f"warning: could not convert {obj.name}: {exc}", file=sys.stderr)
            finally:
                obj.select_set(False)


def render_and_export(*, blend_path: Path, glb_path: Path, preview_path: Path) -> None:
    # Blender 5.1.1 exposes this as BLENDER_EEVEE; older 4.x builds used
    # BLENDER_EEVEE_NEXT. Prefer the enum actually available at runtime.
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    if hasattr(bpy.context.scene, "eevee"):
        bpy.context.scene.eevee.taa_render_samples = 64
    # Use Standard color management for design-review renders: the SLOP blue and
    # green from the SVG need to stay legible, not be washed toward white by Filmic.
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.look = "None"
    bpy.context.scene.render.resolution_x = 1800
    bpy.context.scene.render.resolution_y = 1300
    bpy.context.scene.render.film_transparent = False

    convert_curve_and_text_to_mesh()

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_apply=True,
        export_yup=True,
    )
    bpy.context.scene.render.filepath = str(preview_path)
    bpy.ops.render.render(write_still=True)


def build_primary_scene() -> dict[str, object]:
    clear_scene()
    mats = make_materials()
    add_floor(width=0.72, depth=0.62)

    sloppy_body = import_reachy_assembly(
        collection_name="sloppy_reused_reachy_body_geometry",
        root_matrix=Matrix.Identity(4),
        mats=mats,
        mode="sloppy",
        skip_stems=HEAD_REPLACEMENT_STEMS | ANTENNA_REPLACEMENT_STEMS,
    )
    sloppy_head = create_svg_head(0.0, mats)
    volumes = add_internal_reservation_volumes(0.0, mats)
    add_svg_reference_board(center=(0.170, -0.070, 0.283), height=0.118, mats=mats)

    add_text("SloppyTron v0.3\nReachy body + SVG head", location=(0.0, -0.080, 0.430), size=0.009)
    add_text("front aligned: -Y", location=(-0.145, -0.060, 0.032), size=0.007)
    add_camera_and_light(target=Vector((0.050, 0.0, 0.225)), radius=0.78, z=0.31, focal_length=48)

    all_sloppy = sloppy_body.objects + sloppy_head + volumes
    metrics = {
        "sloppy_bbox_m": bbox_dims(all_sloppy),
        "body_source": "Reachy Mini robot_no_collision.urdf STL body/mechanics; Reachy head/antenna visuals skipped",
        "head_source": str(SLOPPY_SVG),
        "svg_reference_loaded_in_scene": True,
        "orientation": "front faces negative Y; same orientation used for Reachy reference comparison",
        "reachy_body_visuals_imported_for_sloppy": sloppy_body.stats.imported,
        "reachy_body_non_empty_meshes_for_sloppy": sloppy_body.stats.non_empty,
    }

    render_and_export(blend_path=PRIMARY_BLEND, glb_path=PRIMARY_GLB, preview_path=PRIMARY_PREVIEW)
    return metrics


def build_comparison_scene() -> dict[str, object]:
    clear_scene()
    mats = make_materials()
    add_floor(width=1.02, depth=0.66)

    left_offset = -0.18
    right_offset = 0.12
    root_left = Matrix.Translation(Vector((left_offset, 0.0, 0.0)))
    root_right = Matrix.Translation(Vector((right_offset, 0.0, 0.0)))

    sloppy_body = import_reachy_assembly(
        collection_name="comparison_left_sloppy_reused_reachy_body",
        root_matrix=root_left,
        mats=mats,
        mode="sloppy",
        skip_stems=HEAD_REPLACEMENT_STEMS | ANTENNA_REPLACEMENT_STEMS,
    )
    sloppy_head = create_svg_head(left_offset, mats)
    volumes = add_internal_reservation_volumes(left_offset, mats)

    # Same URDF-derived orientation as the Sloppy body. The reference is not
    # mirrored or turned away, fixing the previous comparison readability issue.
    reference = import_reachy_assembly(
        collection_name="comparison_right_reachy_reference_same_orientation",
        root_matrix=root_right,
        mats=mats,
        mode="reference",
    )

    svg_ref = add_svg_reference_board(center=(0.320, -0.075, 0.290), height=0.118, mats=mats)

    add_text("SloppyTron\nSVG head / Reachy body", location=(left_offset, -0.082, 0.430), size=0.0085)
    add_text("Reachy Mini reference\nsame front direction", location=(right_offset, -0.082, 0.430), size=0.0085)
    add_text("fronts aligned toward camera (-Y)", location=(0.0, -0.078, 0.028), size=0.0075)
    add_camera_and_light(target=Vector((0.045, 0.0, 0.225)), radius=1.03, z=0.33, focal_length=42)

    all_sloppy = sloppy_body.objects + sloppy_head + volumes
    metrics = {
        "sloppy_bbox_m": bbox_dims(all_sloppy),
        "reachy_reference_bbox_m": bbox_dims(reference.objects),
        "reachy_reference_visuals_imported": reference.stats.imported,
        "reachy_reference_non_empty_meshes": reference.stats.non_empty,
        "reachy_reference_missing_meshes": reference.stats.missing,
        "reachy_reference_orientation": "same as Sloppy body: URDF front/camera side faces negative Y",
        "svg_reference_loaded_in_scene": len(svg_ref) > 0,
        "sloppy_body_source": "Reachy Mini body/base/Stewart/speaker STL geometry imported from robot_no_collision.urdf",
        "sloppy_head_source": str(SLOPPY_SVG),
        "sloppy_head_strategy": "mascot SVG body/ears/eyes/nose curves scaled onto Reachy head envelope; Reachy head and antenna STL visuals skipped",
        "internal_reserved_volumes": [
            "Pi Camera Module 3: 25 x 24 x 12 mm",
            "XVF3800-style 4-mic array: diameter 65 x 6 mm",
            "5W speaker envelope: diameter 58 x 18 mm",
        ],
    }

    render_and_export(blend_path=COMPARISON_BLEND, glb_path=COMPARISON_GLB, preview_path=COMPARISON_PREVIEW)
    return metrics


def main() -> None:
    ensure_dirs()
    require_inputs()
    primary = build_primary_scene()
    comparison = build_comparison_scene()
    merged = {"primary": primary, "comparison": comparison}
    COMPARISON_METRICS.write_text(json.dumps(merged, indent=2) + "\n")
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
