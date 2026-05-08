import asyncio

from sloppy_tron.provider import create_slop_server
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.ros_bridge import (
    JETSON_HUMBLE,
    PI5_JAZZY,
    BridgeCommand,
    RosBridgeBackend,
    command_from_json,
    command_to_json,
    get_platform,
    platform_ids,
)


class RecordingConnection:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send(self, message: dict) -> None:
        self.messages.append(message)

    def close(self) -> None:
        pass


def test_bridge_command_round_trip() -> None:
    command = BridgeCommand(
        action="look_at_angles",
        params={"pan": 10.0, "tilt": -5.0},
        task_id="task-1",
        created_at=123.0,
    )

    decoded = command_from_json(command_to_json(command))

    assert decoded == command


def test_platform_profiles_capture_runtime_split() -> None:
    assert platform_ids() == ("pi5_jazzy", "jetson_humble")
    assert get_platform("pi5_jazzy") is PI5_JAZZY
    assert get_platform("jetson_humble") is JETSON_HUMBLE
    assert PI5_JAZZY.ros_distro == "jazzy"
    assert PI5_JAZZY.python_version == "3.12"
    assert JETSON_HUMBLE.ros_distro == "humble"
    assert JETSON_HUMBLE.python_version == "3.10"


def test_ros_bridge_backend_publishes_semantic_commands() -> None:
    commands: list[BridgeCommand] = []
    backend = RosBridgeBackend(commands.append)

    task = backend.enable_motion()

    assert task.result == {"accepted": True}
    assert commands == [
        BridgeCommand(
            action="enable_motion",
            params={},
            task_id="ros-task-1",
            created_at=commands[0].created_at,
        )
    ]
    assert backend.snapshot()["tasks"]["ros-task-1"]["name"] == "enable_motion"


def test_ros_bridge_backend_clamps_motion_commands() -> None:
    commands: list[BridgeCommand] = []
    backend = RosBridgeBackend(commands.append)
    fake = FakeBodyBackend()
    fake.enable_motion()
    backend.update_snapshot(fake.snapshot())

    task = backend.look_at_angles(100.0, -100.0)

    assert task.status == "accepted"
    assert task.result == {"accepted": True, "pan": 60.0, "tilt": -35.0}
    assert commands[-1].action == "look_at_angles"
    assert commands[-1].params == {"pan": 60.0, "tilt": -35.0}


def test_ros_bridge_backend_reports_platform_in_state() -> None:
    backend = RosBridgeBackend(lambda command: None, platform=JETSON_HUMBLE)
    state = backend.snapshot()

    assert state["connection"]["backend"] == "ros_bridge"
    assert state["connection"]["platform"] == "jetson_humble"
    assert state["runtime"]["config"]["rosDistro"] == "humble"
    assert state["runtime"]["config"]["pythonVersion"] == "3.10"


def test_ros_bridge_backend_does_not_publish_blocked_motion() -> None:
    commands: list[BridgeCommand] = []
    backend = RosBridgeBackend(commands.append)

    task = backend.look_at_angles(10.0, 10.0)

    assert task.result == {"accepted": False, "pan": 10.0, "tilt": 10.0}
    assert commands == []


def test_slop_server_can_invoke_ros_bridge_backend() -> None:
    commands: list[BridgeCommand] = []
    backend = RosBridgeBackend(commands.append)
    server = create_slop_server(backend)
    conn = RecordingConnection()
    server.handle_connection(conn)

    asyncio.run(
        server.handle_message(
            conn,
            {
                "type": "invoke",
                "id": "enable-1",
                "path": "/safety",
                "action": "enable_motion",
                "params": {},
            },
        )
    )

    assert conn.messages[-1]["status"] == "ok"
    assert commands[-1].action == "enable_motion"
