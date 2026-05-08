import asyncio

from sloppy_tron.provider import FakeBodyBackend, create_slop_server


class RecordingConnection:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send(self, message: dict) -> None:
        self.messages.append(message)

    def close(self) -> None:
        pass


def test_slop_server_exposes_sdk_state_tree() -> None:
    server = create_slop_server()
    tree = server.tree.to_dict()

    assert tree["id"] == "body"
    assert tree["type"] == "root"
    assert _child(tree, "identity")["properties"]["model"] == "v0-dev-rig"
    assert _child(tree, "connection")["type"] == "status"
    assert _child(tree, "pose").get("affordances") is None

    safety_actions = _actions(_child(tree, "safety"))
    assert safety_actions["enable_motion"]["dangerous"] is True
    assert safety_actions["emergency_stop"].get("dangerous", False) is False


def test_slop_server_invokes_actions_through_sdk() -> None:
    server = create_slop_server(FakeBodyBackend())
    conn = RecordingConnection()
    server.handle_connection(conn)

    assert conn.messages[0]["type"] == "hello"
    assert "affordances" in conn.messages[0]["provider"]["capabilities"]

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
    assert conn.messages[-1]["data"]["task"]["result"] == {"accepted": True}
    assert "look_at_angles" in _actions(_child(server.tree.to_dict(), "pose"))

    asyncio.run(
        server.handle_message(
            conn,
            {
                "type": "invoke",
                "id": "look-1",
                "path": "/pose",
                "action": "look_at_angles",
                "params": {"pan": 100.0, "tilt": -100.0},
            },
        )
    )

    assert conn.messages[-1]["status"] == "accepted"
    assert conn.messages[-1]["data"]["taskId"] == "fake-task-2"
    pose = _child(server.tree.to_dict(), "pose")
    assert pose["properties"]["head"] == {"pan": 60.0, "tilt": -35.0}


def test_slop_server_uses_sdk_param_validation() -> None:
    server = create_slop_server(FakeBodyBackend())
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
    asyncio.run(
        server.handle_message(
            conn,
            {
                "type": "invoke",
                "id": "bad-look",
                "path": "/pose",
                "action": "look_at_angles",
                "params": {"pan": 1.0},
            },
        )
    )

    assert conn.messages[-1]["status"] == "error"
    assert conn.messages[-1]["error"]["code"] == "invalid_params"


def _child(tree: dict, node_id: str) -> dict:
    for child in tree["children"]:
        if child["id"] == node_id:
            return child
    raise AssertionError(f"missing child node {node_id}")


def _actions(node: dict) -> dict[str, dict]:
    return {action["action"]: action for action in node.get("affordances", [])}
