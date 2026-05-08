"""Small local CLI for running and inspecting the SLOP body provider."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from slop_ai.transports.stdio import listen as listen_stdio
from slop_ai.transports.unix import listen as listen_unix
from slop_ai.transports.unix import unregister_provider

from sloppy_tron.provider.contract import IdleMode, JsonObject
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.provider.slop_server import create_slop_server
from sloppy_tron.provider.state import coerce_gesture


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sloppy_tron.provider")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("snapshot")
    subparsers.add_parser("tree")
    subparsers.add_parser("serve-stdio")

    unix_parser = subparsers.add_parser("serve-unix")
    unix_parser.add_argument(
        "--socket-path",
        default="/tmp/slop/sloppy-tron-body.sock",
    )
    unix_parser.add_argument("--register", action="store_true")

    subparsers.add_parser("wake")
    subparsers.add_parser("sleep")
    subparsers.add_parser("capture-frame")
    subparsers.add_parser("enable-motion")
    subparsers.add_parser("disable-motion")
    subparsers.add_parser("emergency-stop")

    look_parser = subparsers.add_parser("look-at-angles")
    look_parser.add_argument("--pan", type=float, required=True)
    look_parser.add_argument("--tilt", type=float, required=True)

    gesture_parser = subparsers.add_parser("gesture")
    gesture_parser.add_argument("name")

    idle_parser = subparsers.add_parser("set-idle-mode")
    idle_parser.add_argument("mode", choices=["off", "breathing", "attentive"])

    args = parser.parse_args(argv)
    backend = FakeBodyBackend()
    command = args.command or "serve-stdio"

    if command == "snapshot":
        payload = backend.snapshot()
    elif command == "tree":
        payload = create_slop_server(backend).tree.to_dict()
    elif command == "serve-stdio":
        asyncio.run(listen_stdio(create_slop_server(backend)))
        return 0
    elif command == "serve-unix":
        asyncio.run(_serve_unix(args.socket_path, args.register))
        return 0
    elif command == "wake":
        payload = _task_payload(backend.wake().to_dict(), backend.snapshot())
    elif command == "sleep":
        payload = _task_payload(backend.sleep().to_dict(), backend.snapshot())
    elif command == "capture-frame":
        payload = _task_payload(backend.capture_frame().to_dict(), backend.snapshot())
    elif command == "enable-motion":
        payload = _task_payload(backend.enable_motion().to_dict(), backend.snapshot())
    elif command == "disable-motion":
        payload = _task_payload(backend.disable_motion().to_dict(), backend.snapshot())
    elif command == "emergency-stop":
        payload = _task_payload(backend.emergency_stop().to_dict(), backend.snapshot())
    elif command == "look-at-angles":
        payload = _task_payload(
            backend.look_at_angles(args.pan, args.tilt).to_dict(),
            backend.snapshot(),
        )
    elif command == "gesture":
        payload = _task_payload(
            backend.gesture(coerce_gesture(args.name)).to_dict(),
            backend.snapshot(),
        )
    elif command == "set-idle-mode":
        payload = _task_payload(
            backend.set_idle_mode(_coerce_idle_mode(args.mode)).to_dict(),
            backend.snapshot(),
        )
    else:
        parser.error(f"unsupported command: {command}")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


async def _serve_unix(socket_path: str, register: bool) -> None:
    server = await listen_unix(
        create_slop_server(),
        socket_path,
        register=register,
    )
    try:
        await server.serve_forever()
    finally:
        if register:
            unregister_provider("body")


def _task_payload(task: JsonObject, state: JsonObject) -> JsonObject:
    return {"task": task, "state": state}


def _coerce_idle_mode(value: str) -> IdleMode:
    if value not in {"off", "breathing", "attentive"}:
        msg = f"unsupported idle mode: {value}"
        raise ValueError(msg)
    return value  # type: ignore[return-value]
