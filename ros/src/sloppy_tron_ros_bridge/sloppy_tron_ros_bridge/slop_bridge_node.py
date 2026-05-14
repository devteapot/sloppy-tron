"""ROS node hosting the SLOP body provider bridge."""

from __future__ import annotations

import asyncio
import json
from queue import SimpleQueue
from threading import Thread

import rclpy
from rclpy.node import Node
from slop_ai.transports.unix import listen, unregister_provider
from std_msgs.msg import String

from sloppy_tron.provider import create_slop_server
from sloppy_tron.ros_bridge import (
    BridgeCommand,
    BridgePlatform,
    RosBridgeBackend,
    command_to_json,
    get_platform,
)


class SlopBridgeNode(Node):
    """Bridge ROS body state and commands to a local SLOP provider."""

    def __init__(self, platform: BridgePlatform) -> None:
        super().__init__(f"sloppy_tron_{platform.id}_slop_bridge")
        self._platform = platform
        self.declare_parameter("platform_id", platform.id)
        self.declare_parameter("socket_path", platform.socket_path)
        self.declare_parameter("register_provider", platform.register_provider)
        self.declare_parameter("state_topic", platform.state_topic)
        self.declare_parameter("command_topic", platform.command_topic)

        self._commands: SimpleQueue[BridgeCommand] = SimpleQueue()
        self._backend = RosBridgeBackend(self._commands.put, platform=platform)
        self._slop = create_slop_server(self._backend)

        state_topic = self.get_parameter("state_topic").value
        command_topic = self.get_parameter("command_topic").value
        self._command_publisher = self.create_publisher(String, command_topic, 10)
        self.create_subscription(String, state_topic, self._on_state, 10)
        self.create_timer(0.05, self._drain_commands)

        socket_path = str(self.get_parameter("socket_path").value)
        register_provider = bool(self.get_parameter("register_provider").value)
        self._server_thread = Thread(
            target=self._run_slop_server,
            args=(socket_path, register_provider),
            daemon=True,
        )
        self._server_thread.start()
        self.get_logger().info(
            f"{platform.label} SLOP bridge listening on unix socket {socket_path}"
        )

    def _on_state(self, message: String) -> None:
        try:
            decoded = json.loads(message.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warning(f"Ignoring invalid body_state JSON: {exc}")
            return
        if not isinstance(decoded, dict):
            self.get_logger().warning(
                "Ignoring body_state payload that is not an object"
            )
            return
        self._backend.update_snapshot(decoded)
        self._slop.refresh()

    def _drain_commands(self) -> None:
        if self._command_publisher.get_subscription_count() == 0:
            return
        while not self._commands.empty():
            command = self._commands.get_nowait()
            message = String()
            message.data = command_to_json(command)
            self._command_publisher.publish(message)

    def _run_slop_server(self, socket_path: str, register_provider: bool) -> None:
        async def serve() -> None:
            server = await listen(
                self._slop,
                socket_path,
                register=register_provider,
            )
            try:
                await server.serve_forever()
            finally:
                if register_provider:
                    unregister_provider("body")

        asyncio.run(serve())


def main_for_platform(platform_id: str) -> None:
    rclpy.init()
    node = SlopBridgeNode(get_platform(platform_id))
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main() -> None:
    main_for_platform("pi5_jazzy")


def pi5_jazzy_main() -> None:
    main_for_platform("pi5_jazzy")


def jetson_humble_main() -> None:
    main_for_platform("jetson_humble")
