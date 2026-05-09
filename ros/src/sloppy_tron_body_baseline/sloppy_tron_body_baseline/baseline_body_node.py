"""ROS node exposing the deterministic SloppyTron body baseline."""

from __future__ import annotations

import json
from math import radians

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from sloppy_tron.ros_body_baseline import BaselineBodyModel
from sloppy_tron.ros_bridge import BridgePlatform, command_from_json, get_platform


class BaselineBodyNode(Node):
    """Publish deterministic body state and joint states for the ROS baseline."""

    def __init__(self, platform: BridgePlatform) -> None:
        super().__init__(f"sloppy_tron_{platform.id}_baseline_body")
        self.declare_parameter("platform_id", platform.id)
        self.declare_parameter("state_topic", platform.state_topic)
        self.declare_parameter("command_topic", platform.command_topic)
        self.declare_parameter("joint_state_topic", "joint_states")
        self.declare_parameter("publish_hz", platform.publish_hz)

        self._model = BaselineBodyModel()
        state_topic = str(self.get_parameter("state_topic").value)
        command_topic = str(self.get_parameter("command_topic").value)
        joint_state_topic = str(self.get_parameter("joint_state_topic").value)
        publish_hz = float(self.get_parameter("publish_hz").value)

        self._state_publisher = self.create_publisher(String, state_topic, 10)
        self._joint_state_publisher = self.create_publisher(
            JointState,
            joint_state_topic,
            10,
        )
        self.create_subscription(String, command_topic, self._on_command, 10)
        self.create_timer(1.0 / publish_hz, self._publish)
        self.get_logger().info(
            f"{platform.label} deterministic baseline body publishing {state_topic}"
        )

    def _publish(self) -> None:
        self._publish_state()
        self._publish_joint_state()

    def _publish_state(self) -> None:
        message = String()
        message.data = json.dumps(self._model.snapshot(), sort_keys=True)
        self._state_publisher.publish(message)

    def _publish_joint_state(self) -> None:
        positions = self._model.joint_positions()
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = list(positions)
        message.position = [radians(value) for value in positions.values()]
        self._joint_state_publisher.publish(message)

    def _on_command(self, message: String) -> None:
        try:
            command = command_from_json(message.data)
            self._model.apply_command(
                command.action,
                command.params,
                task_id=command.task_id,
            )
            self._publish()
        except (ValueError, KeyError, TypeError) as exc:
            self.get_logger().warning(f"Ignoring invalid body command: {exc}")


def main_for_platform(platform_id: str) -> None:
    rclpy.init()
    node = BaselineBodyNode(get_platform(platform_id))
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
