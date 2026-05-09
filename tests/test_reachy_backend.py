from __future__ import annotations

import math
from typing import Any

from sloppy_tron.provider import FakeBodyBackend, create_slop_server
from sloppy_tron.provider.reachy_backend import ReachyDaemonBackend


class FakeReachyDaemonClient:
    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any] | None]] = []
        self.status: dict[str, Any] = {
            "robot_name": "reachy_mini",
            "state": "running",
            "simulation_enabled": True,
            "mockup_sim_enabled": False,
            "no_media": True,
            "media_released": False,
            "camera_specs_name": "sim_eye_camera",
            "backend_status": {"motor_control_mode": "enabled", "error": None},
            "error": None,
            "wlan_ip": None,
            "version": "1.7.1",
        }
        self.full_state: dict[str, Any] = {
            "control_mode": "enabled",
            "head_pose": {
                "x": 0.01,
                "y": -0.02,
                "z": 0.03,
                "roll": 0.1,
                "pitch": 0.2,
                "yaw": -0.3,
            },
            "body_yaw": 0.4,
            "antennas_position": [-0.5, 0.6],
            "timestamp": "2026-05-09T12:00:00Z",
        }
        self.media_status: dict[str, Any] = {
            "available": False,
            "released": False,
            "no_media": True,
        }

    def get_json(self, path: str) -> object:
        if path == "/api/daemon/status":
            return self.status
        if path.startswith("/api/state/full"):
            return self.full_state
        if path == "/api/media/status":
            return self.media_status
        raise AssertionError(f"unexpected GET {path}")

    def post_json(self, path: str, payload: dict[str, Any] | None = None) -> object:
        self.posts.append((path, payload))
        if path.startswith("/api/move/"):
            return {"uuid": f"external-{len(self.posts)}"}
        return {"status": "ok"}


class FailingReachyDaemonClient:
    def get_json(self, path: str) -> object:
        raise ConnectionError(f"offline: {path}")

    def post_json(self, path: str, payload: dict[str, Any] | None = None) -> object:
        raise ConnectionError(f"offline: {path}")


def test_reachy_backend_exposes_same_consumer_tree_shape_as_fake_backend() -> None:
    reachy_tree = create_slop_server(
        ReachyDaemonBackend(client=FakeReachyDaemonClient())
    ).tree.to_dict()
    fake_backend = FakeBodyBackend()
    fake_backend.enable_motion()
    fake_tree = create_slop_server(fake_backend).tree.to_dict()

    assert [child["id"] for child in reachy_tree["children"]] == [
        child["id"] for child in fake_tree["children"]
    ]
    assert "identity" not in {child["id"] for child in reachy_tree["children"]}
    assert _actions(_child(reachy_tree, "safety")) == _actions(
        _child(fake_tree, "safety")
    )


def test_reachy_backend_maps_mujoco_daemon_state_into_body_contract() -> None:
    backend = ReachyDaemonBackend(client=FakeReachyDaemonClient())

    state = backend.snapshot()

    assert set(state) == set(FakeBodyBackend().snapshot())
    assert state["connection"]["backend"] == "reachy_daemon"
    assert state["connection"]["bodyBackend"] == "mujoco"
    assert state["connection"]["status"] == "ok"
    assert state["body"]["name"] == "Reachy Mini"
    assert state["body"]["model"] == "reachy-mini-sim"
    assert state["pose"]["bodyYaw"] == math.degrees(0.4)
    assert state["pose"]["antennas"] == {
        "left": math.degrees(-0.5),
        "right": math.degrees(0.6),
    }
    assert state["pose"]["head"] == {
        "pan": math.degrees(-0.3),
        "tilt": math.degrees(0.2),
    }
    assert state["motors"]["mode"] == "enabled"
    assert state["media"]["camera"]["available"] is False
    assert state["safety"]["motionEnabled"] is True
    assert state["runtime"]["config"]["simulationMode"] == "mujoco"


def test_reachy_backend_posts_semantic_motion_to_daemon() -> None:
    client = FakeReachyDaemonClient()
    backend = ReachyDaemonBackend(client=client)

    enable_task = backend.enable_motion()
    look_task = backend.look_at_angles(pan=15.0, tilt=-10.0)
    state = backend.snapshot()

    assert enable_task.result == {"accepted": True}
    assert look_task.status == "accepted"
    assert look_task.result == {
        "accepted": True,
        "pan": 15.0,
        "tilt": -10.0,
        "externalTaskId": "external-2",
    }
    assert client.posts[0] == ("/api/motors/set_mode/enabled", None)
    assert client.posts[1][0] == "/api/move/goto"
    assert client.posts[1][1] == {
        "head_pose": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "roll": 0.0,
            "pitch": math.radians(-10.0),
            "yaw": math.radians(15.0),
        },
        "duration": 0.5,
        "interpolation": "minjerk",
    }
    assert state["tasks"][look_task.task_id]["result"]["externalTaskId"] == "external-2"


def test_reachy_backend_preserves_consumer_contract_when_daemon_is_offline() -> None:
    backend = ReachyDaemonBackend(client=FailingReachyDaemonClient())

    state = backend.snapshot()
    task = backend.wake()

    assert set(state) == set(FakeBodyBackend().snapshot())
    assert state["connection"]["backend"] == "reachy_daemon"
    assert state["connection"]["status"] == "degraded"
    assert state["connection"]["errors"] == [
        "offline: /api/daemon/status",
        "offline: /api/state/full?with_head_joints=true&with_doa=true",
        "offline: /api/media/status",
    ]
    assert task.status == "failed"
    assert task.result == {
        "accepted": False,
        "error": "offline: /api/move/play/wake_up",
    }


def _child(tree: dict[str, Any], node_id: str) -> dict[str, Any]:
    for child in tree["children"]:
        if child["id"] == node_id:
            return child
    raise AssertionError(f"missing child node {node_id}")


def _actions(node: dict[str, Any]) -> list[str]:
    return [action["action"] for action in node.get("affordances", [])]
