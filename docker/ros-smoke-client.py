"""Exercise the ROS-hosted SLOP bridge through its Unix socket."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable
from time import monotonic
from typing import Any

from slop_ai import SlopConsumer
from slop_ai.transports.unix_client import UnixClientTransport

JsonObject = dict[str, Any]
Predicate = Callable[[JsonObject], bool]


async def main() -> None:
    args = _parse_args()
    consumer = SlopConsumer(UnixClientTransport(args.socket_path), timeout=args.timeout)

    hello = await consumer.connect()
    provider = _object(hello, "provider")
    _assert(provider.get("id") == "body", f"unexpected provider hello: {hello}")
    print(f"connected to SLOP provider {provider['id']!r} on {args.platform_id}")

    await _wait_for_node(
        consumer,
        "/safety",
        lambda node: "enable_motion" in _affordance_names(node),
        "safety affordance enable_motion to appear",
        args.timeout,
    )

    enable = await consumer.invoke("/safety", "enable_motion", {})
    _assert(enable["status"] == "ok", f"enable_motion failed: {enable}")
    _assert(
        _object(_object(enable, "data"), "task")["result"] == {"accepted": True},
        f"enable_motion was not accepted: {enable}",
    )
    print("invoked enable_motion")

    await _wait_for_node(
        consumer,
        "/safety",
        lambda node: bool(_object(node, "properties")["motionEnabled"]),
        "motionEnabled state to become true",
        args.timeout,
    )
    await _wait_for_node(
        consumer,
        "/pose",
        lambda node: "look_at_angles" in _affordance_names(node),
        "pose affordance look_at_angles to appear",
        args.timeout,
    )

    look = await consumer.invoke(
        "/pose",
        "look_at_angles",
        {"pan": args.pan, "tilt": args.tilt},
    )
    _assert(look["status"] == "accepted", f"look_at_angles failed: {look}")
    print(f"invoked look_at_angles pan={args.pan} tilt={args.tilt}")

    pose = await _wait_for_node(
        consumer,
        "/pose",
        lambda node: _head_matches(node, args.pan, args.tilt),
        "pose head target to reflect look_at_angles",
        args.timeout,
    )
    head = _object(_object(pose, "properties"), "head")
    print(f"verified pose pan={head['pan']} tilt={head['tilt']}")

    consumer.disconnect()
    await asyncio.sleep(0)


async def _wait_for_node(
    consumer: SlopConsumer,
    path: str,
    predicate: Predicate,
    description: str,
    timeout: float,
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("socket_path")
    parser.add_argument("platform_id")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--pan", type=float, default=32.0)
    parser.add_argument("--tilt", type=float, default=-14.0)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
