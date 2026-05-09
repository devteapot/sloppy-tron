#!/usr/bin/env python3
"""Smoke client for a running Reachy Mini daemon via SloppyTron SLOP backend."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from sloppy_tron.provider.reachy_backend import ReachyDaemonBackend


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--pan", type=float, default=10.0)
    parser.add_argument("--tilt", type=float, default=-5.0)
    args = parser.parse_args()

    backend = ReachyDaemonBackend(host=args.host, port=args.port)
    initial = backend.snapshot()
    _require(initial["connection"]["backend"] == "reachy_daemon", initial)
    _require(initial["connection"]["status"] == "ok", initial)

    enable = backend.enable_motion()
    _require(enable.status != "failed", enable.to_dict())

    look = backend.look_at_angles(args.pan, args.tilt)
    _require(look.status != "failed", look.to_dict())

    final = backend.snapshot()
    _require(final["connection"]["backend"] == "reachy_daemon", final)
    _require(final["body"]["name"] == "Reachy Mini", final)

    print(
        json.dumps(
            {
                "backend": final["connection"].get("bodyBackend"),
                "status": final["connection"].get("status"),
                "enableTask": enable.to_dict(),
                "lookTask": look.to_dict(),
                "pose": final["pose"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _require(condition: bool, payload: Any) -> None:
    if not condition:
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
