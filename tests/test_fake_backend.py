from sloppy_tron.provider import AFFORDANCES, PROVIDER_ID, FakeBodyBackend
from sloppy_tron.provider.state import coerce_gesture


def test_provider_metadata_matches_contract() -> None:
    assert PROVIDER_ID == "body"


def test_fake_backend_exposes_full_state_tree() -> None:
    state = FakeBodyBackend().snapshot()

    assert set(state) == {
        "connection",
        "body",
        "pose",
        "motors",
        "media",
        "audio",
        "vision",
        "expression",
        "safety",
        "tasks",
        "calibration",
        "runtime",
    }
    assert state["connection"]["backend"] == "fake"
    assert state["safety"]["motionEnabled"] is False
    assert state["safety"]["privacy"]["remoteAccess"] == "disabled"


def test_affordances_mark_risky_controls() -> None:
    risks = {affordance.name: affordance.risk for affordance in AFFORDANCES}

    assert risks["wake"] == "safe"
    assert risks["look_at_angles"] == "safe"
    assert risks["emergency_stop"] == "safe"
    assert risks["enable_motion"] == "guarded"
    assert risks["disable_motion"] == "guarded"
    assert risks["raw_motor_command"] == "dangerous"
    assert risks["emergency_stop_reset"] == "dangerous"


def test_motion_clamps_to_configured_limits() -> None:
    backend = FakeBodyBackend()
    backend.enable_motion()

    task = backend.look_at_angles(pan=100.0, tilt=-100.0)
    state = backend.snapshot()

    assert task.result == {"accepted": True, "pan": 60.0, "tilt": -35.0}
    assert state["pose"]["head"] == {"pan": 60.0, "tilt": -35.0}
    assert state["tasks"][task.task_id]["status"] == "succeeded"


def test_disabled_motion_does_not_move_pose() -> None:
    backend = FakeBodyBackend()

    task = backend.look_at_angles(pan=20.0, tilt=10.0)
    state = backend.snapshot()

    assert task.result == {"accepted": False, "pan": 20.0, "tilt": 10.0}
    assert state["pose"]["head"] == {"pan": 0.0, "tilt": 0.0}


def test_emergency_stop_prevents_motion_enable() -> None:
    backend = FakeBodyBackend()
    backend.emergency_stop()

    task = backend.enable_motion()
    state = backend.snapshot()

    assert task.result == {"accepted": False}
    assert state["safety"]["motionEnabled"] is False
    assert state["safety"]["eStop"] is True


def test_capture_frame_requires_media_ownership() -> None:
    backend = FakeBodyBackend()

    task = backend.capture_frame()
    state = backend.snapshot()

    assert task.result == {"captured": True}
    assert state["vision"]["frameAvailable"] is True
    assert state["vision"]["privacyMode"] == "local_explicit_capture_only"


def test_fake_backend_can_preserve_external_task_id() -> None:
    backend = FakeBodyBackend()
    backend.enable_motion()

    task = backend.look_at_angles(10.0, -5.0, task_id="ros-task-42")
    state = backend.snapshot()

    assert task.task_id == "ros-task-42"
    assert state["tasks"]["ros-task-42"]["name"] == "look_at_angles"
    assert state["tasks"]["ros-task-42"]["result"] == {
        "accepted": True,
        "pan": 10.0,
        "tilt": -5.0,
    }


def test_gesture_validation_rejects_unknown_names() -> None:
    assert coerce_gesture("nod") == "nod"

    try:
        coerce_gesture("spin")
    except ValueError as exc:
        assert "unsupported gesture" in str(exc)
    else:
        raise AssertionError("expected unknown gesture to raise")
