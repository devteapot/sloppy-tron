from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION_ROOT = REPO_ROOT / "ros" / "src" / "sloppy_tron_description"
URDF = DESCRIPTION_ROOT / "urdf" / "sloppy_tron_v0.urdf.xacro"


def test_sloppy_tron_v0_description_preserves_contract_joints() -> None:
    root = ElementTree.parse(URDF).getroot()
    joints = {joint.attrib["name"] for joint in root.findall("joint")}

    assert {
        "body_yaw_joint",
        "head_pan_joint",
        "head_tilt_joint",
        "antenna_left_joint",
        "antenna_right_joint",
    } <= joints


def test_sloppy_tron_v0_description_uses_mascot_palette() -> None:
    root = ElementTree.parse(URDF).getroot()
    materials = {
        material.attrib["name"]: material.find("color").attrib["rgba"]
        for material in root.findall("material")
    }

    assert materials["slop_blue"] == "0.290 0.561 0.906 1.0"
    assert materials["slop_dark_blue"] == "0.169 0.502 0.812 1.0"
    assert materials["slop_eye_green"] == "0.596 0.961 0.651 1.0"
    assert materials["feature_black"] == "0.0 0.0 0.0 1.0"


def test_sloppy_tron_v0_mesh_references_exist() -> None:
    root = ElementTree.parse(URDF).getroot()
    mesh_filenames = [
        mesh.attrib["filename"]
        for mesh in root.findall(".//mesh")
        if mesh.attrib["filename"].startswith("package://sloppy_tron_description/")
    ]

    assert mesh_filenames
    for filename in mesh_filenames:
        relative = filename.removeprefix("package://sloppy_tron_description/")
        assert (DESCRIPTION_ROOT / relative).exists(), filename


def test_body_design_doc_names_sloppy_svg_reference() -> None:
    design_doc = (REPO_ROOT / "docs" / "sloppytron-v0-body-design.md").read_text()

    assert "~/dev/slop/logo/sloppy.svg" in design_doc
    assert "#4A8FE7" in design_doc
    assert "#98F5A6" in design_doc
