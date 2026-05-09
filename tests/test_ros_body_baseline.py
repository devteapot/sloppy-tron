from __future__ import annotations

from sloppy_tron.ros_body_baseline import BaselineBodyModel


def test_baseline_snapshot_exposes_reachy_compatible_body_shape() -> None:
    model = BaselineBodyModel()

    snapshot = model.snapshot()

    assert snapshot["connection"]["backend"] == "ros_baseline"
    assert snapshot["body"] == {
        "name": "SloppyTron ROS Baseline",
        "model": "reachy-compatible-kinematic-baseline",
        "coordinateFrame": "head_pan_tilt_degrees_body_yaw_degrees",
        "capabilities": [
            "wake",
            "sleep",
            "look_at_angles",
            "look_at_point",
            "gesture",
            "capture_frame",
            "safety_state",
            "body_yaw",
            "antennas",
        ],
    }
    assert snapshot["pose"]["bodyYaw"] == 0.0
    assert snapshot["pose"]["antennas"] == {"left": 0.0, "right": 0.0}
    assert snapshot["motors"]["bus"] == "ros_baseline"
    assert [device["name"] for device in snapshot["motors"]["devices"]] == [
        "body_yaw",
        "head_pan",
        "head_tilt",
        "antenna_left",
        "antenna_right",
    ]


def test_baseline_enable_motion_preserves_bridge_task_id() -> None:
    model = BaselineBodyModel()

    task = model.apply_command("enable_motion", {}, task_id="ros-task-42")
    snapshot = model.snapshot()

    assert task.task_id == "ros-task-42"
    assert task.status == "succeeded"
    assert task.result == {"accepted": True}
    assert snapshot["safety"]["motionEnabled"] is True
    assert snapshot["tasks"]["ros-task-42"]["taskId"] == "ros-task-42"


def test_baseline_look_at_angles_clamps_pose_and_updates_joint_positions() -> None:
    model = BaselineBodyModel()
    model.apply_command("enable_motion", {}, task_id="enable-task")

    task = model.apply_command(
        "look_at_angles",
        {"pan": 120.0, "tilt": -90.0},
        task_id="look-task",
    )
    snapshot = model.snapshot()

    assert task.task_id == "look-task"
    assert task.result == {"accepted": True, "pan": 60.0, "tilt": -35.0}
    assert snapshot["pose"]["head"] == {"pan": 60.0, "tilt": -35.0}
    assert snapshot["pose"]["target"] == {"pan": 60.0, "tilt": -35.0}
    assert model.joint_positions() == {
        "body_yaw_joint": 0.0,
        "head_pan_joint": 60.0,
        "head_tilt_joint": -35.0,
        "antenna_left_joint": 0.0,
        "antenna_right_joint": 0.0,
    }


def test_baseline_rejects_motion_commands_when_motion_is_disabled() -> None:
    model = BaselineBodyModel()

    task = model.apply_command(
        "look_at_angles",
        {"pan": 15.0, "tilt": 10.0},
        task_id="blocked-task",
    )
    snapshot = model.snapshot()

    assert task.status == "failed"
    assert task.result == {"accepted": False, "reason": "motion_disabled"}
    assert snapshot["pose"]["head"] == {"pan": 0.0, "tilt": 0.0}
    assert snapshot["tasks"]["blocked-task"]["status"] == "failed"


def test_baseline_gestures_drive_reachy_like_expression_and_antennas() -> None:
    model = BaselineBodyModel()
    model.apply_command("enable_motion", {}, task_id="enable-task")

    model.apply_command("gesture", {"gesture": "curious_tilt"}, task_id="gesture-task")
    snapshot = model.snapshot()

    assert snapshot["expression"]["current"] == "curious_tilt"
    assert snapshot["pose"]["head"] == {"pan": 0.0, "tilt": 12.0}
    assert snapshot["pose"]["antennas"] == {"left": 18.0, "right": -18.0}

    model.apply_command("sleep", {}, task_id="sleep-task")
    snapshot = model.snapshot()

    assert snapshot["safety"]["motionEnabled"] is False
    assert snapshot["expression"]["current"] == "sleep"
    assert snapshot["pose"]["head"] == {"pan": 0.0, "tilt": 0.0}
    assert snapshot["pose"]["antennas"] == {"left": 0.0, "right": 0.0}
