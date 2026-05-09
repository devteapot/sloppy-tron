import asyncio

from sloppy_tron.provider import FakeBodyBackend, create_slop_server
from sloppy_tron.provider.contract import (
    AFFORDANCES,
    FUTURE_AFFORDANCE_NAMES,
    IMPLEMENTED_AFFORDANCE_NAMES,
)


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
    assert _child(tree, "body")["properties"]["model"] == "v0-dev-rig"
    assert "identity" not in {child["id"] for child in tree["children"]}
    assert _child(tree, "connection")["type"] == "status"
    assert _child(tree, "pose").get("affordances") is None

    safety_actions = _actions(_child(tree, "safety"))
    assert safety_actions["enable_motion"]["dangerous"] is True
    assert safety_actions["emergency_stop"].get("dangerous", False) is False


def test_contract_affordance_classification_is_explicit() -> None:
    all_affordance_names = {affordance.name for affordance in AFFORDANCES}

    assert IMPLEMENTED_AFFORDANCE_NAMES
    assert FUTURE_AFFORDANCE_NAMES
    assert IMPLEMENTED_AFFORDANCE_NAMES.isdisjoint(FUTURE_AFFORDANCE_NAMES)
    classified_names = IMPLEMENTED_AFFORDANCE_NAMES | FUTURE_AFFORDANCE_NAMES
    assert all_affordance_names == classified_names


def test_implemented_affordances_are_exposed_across_representative_states() -> None:
    default_backend = FakeBodyBackend()
    motion_backend = FakeBodyBackend()
    motion_backend.enable_motion()
    media_released_backend = FakeBodyBackend()
    media_released_backend.release_media()

    exposed = set().union(
        _exposed_actions(default_backend),
        _exposed_actions(motion_backend),
        _exposed_actions(media_released_backend),
    )

    assert exposed >= IMPLEMENTED_AFFORDANCE_NAMES
    assert exposed.isdisjoint(FUTURE_AFFORDANCE_NAMES)


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


def _exposed_actions(backend: FakeBodyBackend) -> set[str]:
    tree = create_slop_server(backend).tree.to_dict()
    actions: set[str] = set()
    for child in tree["children"]:
        actions.update(_actions(child))
    return actions
