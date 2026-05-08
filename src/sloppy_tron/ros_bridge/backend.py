"""Backend implementation that bridges SLOP actions into ROS commands."""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from itertools import count
from time import time
from typing import cast

from sloppy_tron.provider.contract import BodyGesture, IdleMode, JsonObject
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.provider.state import TaskState
from sloppy_tron.ros_bridge.commands import BridgeCommand
from sloppy_tron.ros_bridge.platforms import PI5_JAZZY, BridgePlatform

CommandSink = Callable[[BridgeCommand], None]


class RosBridgeBackend:
    """SLOP backend backed by ROS state snapshots and command publication."""

    def __init__(
        self,
        command_sink: CommandSink,
        platform: BridgePlatform = PI5_JAZZY,
    ) -> None:
        initial_state = FakeBodyBackend().snapshot()
        connection = _object_section(initial_state, "connection")
        connection["backend"] = "ros_bridge"
        connection["platform"] = platform.id
        runtime = _object_section(initial_state, "runtime")
        config = _object_section(runtime, "config")
        config.update(
            {
                "platform": platform.id,
                "board": platform.board,
                "rosDistro": platform.ros_distro,
                "ubuntuVersion": platform.ubuntu_version,
                "pythonVersion": platform.python_version,
            }
        )
        self._state = initial_state
        self._command_sink = command_sink
        self._platform = platform
        self._task_numbers = count(1)

    def snapshot(self) -> JsonObject:
        return copy.deepcopy(self._state)

    def update_snapshot(self, snapshot: Mapping[str, object]) -> None:
        self._state = copy.deepcopy(cast(JsonObject, dict(snapshot)))

    def wake(self) -> TaskState:
        return self._issue("wake", {"posture": "awake"}, async_task=True)

    def sleep(self) -> TaskState:
        return self._issue("sleep", {"posture": "sleep"}, async_task=True)

    def look_at_angles(self, pan: float, tilt: float) -> TaskState:
        clamped_pan = self._clamp_axis("pan", pan)
        clamped_tilt = self._clamp_axis("tilt", tilt)
        accepted = self._motion_can_run()
        return self._issue(
            "look_at_angles",
            {"pan": clamped_pan, "tilt": clamped_tilt},
            result={"accepted": accepted, "pan": clamped_pan, "tilt": clamped_tilt},
            publish=accepted,
            async_task=True,
        )

    def look_at_point(self, x: float, y: float, z: float) -> TaskState:
        accepted = self._motion_can_run()
        return self._issue(
            "look_at_point",
            {"x": x, "y": y, "z": z},
            result={"accepted": accepted},
            publish=accepted,
            async_task=True,
        )

    def look_toward_sound(self) -> TaskState:
        accepted = self._motion_can_run()
        return self._issue(
            "look_toward_sound",
            {"directionOfArrival": None},
            result={"accepted": accepted},
            publish=accepted,
            async_task=True,
        )

    def gesture(self, gesture: BodyGesture) -> TaskState:
        return self._issue("gesture", {"gesture": gesture}, async_task=True)

    def capture_frame(self) -> TaskState:
        released = bool(_object_section(self._state, "media").get("released", False))
        return self._issue(
            "capture_frame",
            {},
            result={"captured": not released},
            publish=not released,
        )

    def set_idle_mode(self, idle_mode: IdleMode) -> TaskState:
        return self._issue("set_idle_mode", {"idleMode": idle_mode})

    def release_media(self) -> TaskState:
        return self._issue("release_media", {}, result={"released": True})

    def acquire_media(self) -> TaskState:
        return self._issue("acquire_media", {}, result={"released": False})

    def enable_motion(self) -> TaskState:
        accepted = not bool(_object_section(self._state, "safety").get("eStop", False))
        return self._issue(
            "enable_motion", {}, result={"accepted": accepted}, publish=accepted
        )

    def disable_motion(self) -> TaskState:
        _object_section(self._state, "safety")["motionEnabled"] = False
        return self._issue("disable_motion", {}, result={"accepted": True})

    def emergency_stop(self) -> TaskState:
        safety = _object_section(self._state, "safety")
        safety["motionEnabled"] = False
        safety["eStop"] = True
        return self._issue("emergency_stop", {}, result={"accepted": True})

    def _issue(
        self,
        action: str,
        target: JsonObject,
        *,
        result: JsonObject | None = None,
        publish: bool = True,
        async_task: bool = False,
    ) -> TaskState:
        task = self._make_task(action, target, result)
        self._store_task(task)
        if publish:
            self._command_sink(
                BridgeCommand(
                    action=action,
                    params=target,
                    task_id=task.task_id,
                    created_at=task.started_at,
                )
            )
        if async_task:
            task.status = "accepted"
            task.progress = 0.0
            task.completed_at = None
            self._store_task(task)
        return task

    def _make_task(
        self,
        action: str,
        target: JsonObject,
        result: JsonObject | None,
    ) -> TaskState:
        now = time()
        return TaskState(
            task_id=f"ros-task-{next(self._task_numbers)}",
            name=action,
            status="succeeded",
            progress=1.0,
            target=target,
            started_at=now,
            completed_at=now,
            result={} if result is None else result,
        )

    def _store_task(self, task: TaskState) -> None:
        tasks = _object_section(self._state, "tasks")
        tasks[task.task_id] = task.to_dict()
        _object_section(self._state, "connection")["lastSeenAt"] = time()

    def _motion_can_run(self) -> bool:
        safety = _object_section(self._state, "safety")
        return bool(safety.get("motionEnabled", False)) and not bool(
            safety.get("eStop", False)
        )

    def _clamp_axis(self, axis: str, value: float) -> float:
        pose = _object_section(self._state, "pose")
        limits = _object_section(pose, "limits")
        axis_limits = _object_section(limits, axis)
        minimum = _number(axis_limits.get("min"), -180.0)
        maximum = _number(axis_limits.get("max"), 180.0)
        return min(max(value, minimum), maximum)


def _object_section(data: JsonObject, name: str) -> JsonObject:
    section = data.get(name)
    if isinstance(section, dict):
        return section
    section = {}
    data[name] = section
    return section


def _number(value: object, default: float) -> float:
    if isinstance(value, int | float):
        return float(value)
    return default
