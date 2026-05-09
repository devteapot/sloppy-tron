"""Fake ROS body node for exercising the SLOP bridge without hardware."""

from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from sloppy_tron.provider.contract import IdleMode
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.provider.state import coerce_gesture
from sloppy_tron.ros_bridge import BridgePlatform, command_from_json, get_platform


class FakeBodyNode(Node):
    """Publish fake body state and execute semantic bridge commands."""

    def __init__(self, platform: BridgePlatform) -> None:
        super().__init__(f"sloppy_tron_{platform.id}_fake_body")
        self.declare_parameter("platform_id", platform.id)
        self.declare_parameter("state_topic", platform.state_topic)
        self.declare_parameter("command_topic", platform.command_topic)
        self.declare_parameter("publish_hz", platform.publish_hz)

        self._backend = FakeBodyBackend()
        state_topic = self.get_parameter("state_topic").value
        command_topic = self.get_parameter("command_topic").value
        publish_hz = float(self.get_parameter("publish_hz").value)

        self._state_publisher = self.create_publisher(String, state_topic, 10)
        self.create_subscription(String, command_topic, self._on_command, 10)
        self.create_timer(1.0 / publish_hz, self._publish_state)

    def _publish_state(self) -> None:
        message = String()
        message.data = json.dumps(self._backend.snapshot(), sort_keys=True)
        self._state_publisher.publish(message)

    def _on_command(self, message: String) -> None:
        try:
            command = command_from_json(message.data)
            self._apply_command(command.action, command.params, command.task_id)
        except (ValueError, KeyError, TypeError) as exc:
            self.get_logger().warning(f"Ignoring invalid body command: {exc}")

    def _apply_command(self, action: str, params: dict, task_id: str) -> None:
        if action == "wake":
            self._backend.wake(task_id=task_id)
        elif action == "sleep":
            self._backend.sleep(task_id=task_id)
        elif action == "look_at_angles":
            self._backend.look_at_angles(
                float(params["pan"]),
                float(params["tilt"]),
                task_id=task_id,
            )
        elif action == "look_at_point":
            self._backend.look_at_point(
                float(params["x"]),
                float(params["y"]),
                float(params["z"]),
                task_id=task_id,
            )
        elif action == "look_toward_sound":
            self._backend.look_toward_sound(task_id=task_id)
        elif action == "gesture":
            self._backend.gesture(
                coerce_gesture(str(params["gesture"])),
                task_id=task_id,
            )
        elif action == "capture_frame":
            self._backend.capture_frame(task_id=task_id)
        elif action == "set_idle_mode":
            self._backend.set_idle_mode(
                _coerce_idle_mode(str(params["idleMode"])),
                task_id=task_id,
            )
        elif action == "release_media":
            self._backend.release_media(task_id=task_id)
        elif action == "acquire_media":
            self._backend.acquire_media(task_id=task_id)
        elif action == "enable_motion":
            self._backend.enable_motion(task_id=task_id)
        elif action == "disable_motion":
            self._backend.disable_motion(task_id=task_id)
        elif action == "emergency_stop":
            self._backend.emergency_stop(task_id=task_id)
        else:
            raise ValueError(f"unsupported body command action: {action}")


def _coerce_idle_mode(value: str) -> IdleMode:
    if value not in {"off", "breathing", "attentive"}:
        raise ValueError(f"unsupported idle mode: {value}")
    return value  # type: ignore[return-value]


def main_for_platform(platform_id: str) -> None:
    rclpy.init()
    node = FakeBodyNode(get_platform(platform_id))
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main() -> None:
    main_for_platform("pi5_jazzy")


def pi5_jazzy_main() -> None:
    main_for_platform("pi5_jazzy")


def jetson_humble_main() -> None:
    main_for_platform("jetson_humble")
