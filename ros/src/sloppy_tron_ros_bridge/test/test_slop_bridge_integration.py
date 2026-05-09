"""Launch test for the fake body to SLOP bridge runtime loop."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from collections.abc import Callable
from pathlib import Path
from time import monotonic
from typing import Any

import launch
import launch_ros.actions
import launch_testing
import pytest
from launch_testing.asserts import assertExitCodes
from slop_ai import SlopConsumer
from slop_ai.transports.unix_client import UnixClientTransport

JsonObject = dict[str, Any]
Predicate = Callable[[JsonObject], bool]


@pytest.mark.launch_test
def generate_test_description() -> tuple[launch.LaunchDescription, dict[str, Any]]:
    platform_id, fake_exec, bridge_exec = _platform_from_ros_distro()
    suffix = f"{platform_id}_{os.getpid()}"
    socket_path = f"/tmp/slop/sloppy-tron-integration-{suffix}.sock"

    Path(socket_path).unlink(missing_ok=True)

    fake_body = launch_ros.actions.Node(
        package="sloppy_tron_ros_bridge",
        executable=fake_exec,
        output="screen",
        parameters=[{"publish_hz": 20.0}],
    )
    slop_bridge = launch_ros.actions.Node(
        package="sloppy_tron_ros_bridge",
        executable=bridge_exec,
        output="screen",
        parameters=[
            {
                "socket_path": socket_path,
                "register_provider": False,
            }
        ],
    )

    return (
        launch.LaunchDescription(
            [
                fake_body,
                slop_bridge,
                launch_testing.actions.ReadyToTest(),
            ]
        ),
        {
            "fake_body": fake_body,
            "platform_id": platform_id,
            "slop_bridge": slop_bridge,
            "socket_path": socket_path,
        },
    )


class TestSlopBridgeIntegration(unittest.TestCase):
    def test_fake_body_round_trip(
        self,
        proc_info: Any,
        fake_body: launch_ros.actions.Node,
        slop_bridge: launch_ros.actions.Node,
        socket_path: str,
        platform_id: str,
    ) -> None:
        proc_info.assertWaitForStartup(process=fake_body, timeout=10)
        proc_info.assertWaitForStartup(process=slop_bridge, timeout=10)

        asyncio.run(_exercise_slop_bridge(socket_path, platform_id))


@launch_testing.post_shutdown_test()
class TestSlopBridgeShutdown(unittest.TestCase):
    def test_processes_exit_cleanly(self, proc_info: Any) -> None:
        assertExitCodes(proc_info)

    def test_socket_is_removed(self, socket_path: str) -> None:
        Path(socket_path).unlink(missing_ok=True)


async def _exercise_slop_bridge(socket_path: str, platform_id: str) -> None:
    await _wait_for_socket(socket_path, timeout=10.0)
    consumer = SlopConsumer(UnixClientTransport(socket_path), timeout=10.0)

    hello = await consumer.connect()
    provider = _object(hello, "provider")
    _assert(provider.get("id") == "body", f"unexpected provider hello: {hello}")

    await _wait_for_node(
        consumer,
        "/safety",
        lambda node: "enable_motion" in _affordance_names(node),
        "safety affordance enable_motion to appear",
    )

    enable = await consumer.invoke("/safety", "enable_motion", {})
    _assert(enable["status"] == "ok", f"enable_motion failed: {enable}")
    _assert(
        _object(_object(enable, "data"), "task")["result"] == {"accepted": True},
        f"enable_motion was not accepted: {enable}",
    )

    await _wait_for_node(
        consumer,
        "/safety",
        lambda node: bool(_object(node, "properties")["motionEnabled"]),
        "motionEnabled state to become true",
    )

    pose = await _wait_for_node(
        consumer,
        "/pose",
        lambda node: "look_at_angles" in _affordance_names(node),
        "pose affordance look_at_angles to appear",
    )
    runtime = await consumer.query("/runtime", depth=-1)
    runtime_config = _object(_object(runtime.to_dict(), "properties"), "config")
    _assert(
        runtime_config["platform"] == platform_id,
        f"bridge advertised wrong platform: {runtime_config}",
    )

    look = await consumer.invoke(
        "/pose",
        "look_at_angles",
        {"pan": 32.0, "tilt": -14.0},
    )
    _assert(look["status"] == "accepted", f"look_at_angles failed: {look}")

    pose = await _wait_for_node(
        consumer,
        "/pose",
        lambda node: _head_matches(node, pan=32.0, tilt=-14.0),
        "pose head target to reflect look_at_angles",
    )
    head = _object(_object(pose, "properties"), "head")
    _assert(head == {"pan": 32.0, "tilt": -14.0}, f"unexpected final pose: {pose}")

    consumer.disconnect()
    await asyncio.sleep(0)


async def _wait_for_socket(socket_path: str, timeout: float) -> None:
    deadline = monotonic() + timeout
    path = Path(socket_path)
    while monotonic() < deadline:
        if path.is_socket():
            return
        await asyncio.sleep(0.1)
    raise AssertionError(f"timed out waiting for SLOP socket {socket_path}")


async def _wait_for_node(
    consumer: SlopConsumer,
    path: str,
    predicate: Predicate,
    description: str,
    timeout: float = 10.0,
) -> JsonObject:
    deadline = monotonic() + timeout
    last: JsonObject | None = None
    while monotonic() < deadline:
        node = (await consumer.query(path, depth=-1)).to_dict()
        last = node
        if predicate(node):
            return node
        await asyncio.sleep(0.2)

    preview = json.dumps(last, sort_keys=True)[:1000] if last is not None else "null"
    raise AssertionError(f"timed out waiting for {description}; last={preview}")


def _platform_from_ros_distro() -> tuple[str, str, str]:
    distro = os.environ.get("ROS_DISTRO")
    if distro == "jazzy":
        return "pi5_jazzy", "fake_body_pi5_jazzy", "slop_bridge_pi5_jazzy"
    if distro == "humble":
        return "jetson_humble", "fake_body_jetson_humble", "slop_bridge_jetson_humble"
    raise RuntimeError(f"unsupported ROS_DISTRO for integration test: {distro!r}")


def _affordance_names(node: JsonObject) -> set[str]:
    affordances = node.get("affordances")
    if not isinstance(affordances, list):
        return set()
    return {
        str(affordance["action"])
        for affordance in affordances
        if isinstance(affordance, dict) and isinstance(affordance.get("action"), str)
    }


def _head_matches(node: JsonObject, pan: float, tilt: float) -> bool:
    head = _object(_object(node, "properties"), "head")
    return (
        abs(float(head["pan"]) - pan) < 0.001
        and abs(float(head["tilt"]) - tilt) < 0.001
    )


def _object(data: JsonObject, key: str) -> JsonObject:
    value = data.get(key)
    if not isinstance(value, dict):
        raise AssertionError(f"expected {key!r} to be an object in {data}")
    return value


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
