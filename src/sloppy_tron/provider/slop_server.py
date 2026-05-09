"""SLOP SDK adapter for the SloppyTron body provider."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, cast

from slop_ai import SlopServer

from sloppy_tron.provider.backend import BodyBackend
from sloppy_tron.provider.contract import (
    PROVIDER_ID,
    BodyGesture,
    IdleMode,
)
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.provider.state import TaskState, coerce_gesture

Descriptor = dict[str, Any]
Handler = Callable[..., dict[str, Any]]

GESTURE_VALUES: tuple[BodyGesture, ...] = (
    "nod",
    "shake_no",
    "curious_tilt",
    "look_away",
    "look_back",
    "wake",
    "sleep",
    "idle_breathe",
    "small_ack",
)
IDLE_MODE_VALUES: tuple[IdleMode, ...] = ("off", "breathing", "attentive")


class SlopConflictError(Exception):
    """Raised when a stale affordance is invoked after state changed."""

    code = "conflict"


def create_slop_server(backend: BodyBackend | None = None) -> SlopServer:
    """Create a SLOP SDK server backed by the fake body backend."""

    body = backend or FakeBodyBackend()
    server = SlopServer(PROVIDER_ID, "SloppyTron Body")

    def _refresh() -> dict[str, Any]:
        return {"version": server.version}

    def _snapshot() -> dict[str, Any]:
        return body.snapshot()

    def _wake() -> dict[str, Any]:
        _raise_if_estopped(body)
        return _async_task(body.wake())

    def _sleep() -> dict[str, Any]:
        return _async_task(body.sleep())

    def _look_at_angles(pan: float, tilt: float) -> dict[str, Any]:
        _raise_if_motion_blocked(body)
        return _async_task(body.look_at_angles(pan=pan, tilt=tilt))

    def _look_at_point(x: float, y: float, z: float) -> dict[str, Any]:
        _raise_if_motion_blocked(body)
        return _async_task(body.look_at_point(x=x, y=y, z=z))

    def _look_toward_sound() -> dict[str, Any]:
        _raise_if_motion_blocked(body)
        return _async_task(body.look_toward_sound())

    def _gesture(name: str) -> dict[str, Any]:
        gesture = coerce_gesture(name)
        if gesture != "sleep":
            _raise_if_estopped(body)
        return _async_task(body.gesture(gesture))

    def _capture_frame() -> dict[str, Any]:
        if _section(body.snapshot(), "media")["released"]:
            raise SlopConflictError("media is released")
        return _task_result(body.capture_frame())

    def _set_idle_mode(mode: str) -> dict[str, Any]:
        return _task_result(body.set_idle_mode(_coerce_idle_mode(mode)))

    def _release_media() -> dict[str, Any]:
        return _task_result(body.release_media())

    def _acquire_media() -> dict[str, Any]:
        return _task_result(body.acquire_media())

    def _enable_motion() -> dict[str, Any]:
        _raise_if_estopped(body)
        return _task_result(body.enable_motion())

    def _disable_motion() -> dict[str, Any]:
        return _task_result(body.disable_motion())

    def _emergency_stop() -> dict[str, Any]:
        return _task_result(body.emergency_stop())

    def connection_node() -> Descriptor:
        state = body.snapshot()
        connection = _section(state, "connection")
        return {
            "type": "status",
            "props": connection,
            "summary": f"{connection['backend']} backend is {connection['status']}",
            "actions": {
                "refresh": _action(
                    _refresh,
                    "Refresh cached body state.",
                    idempotent=True,
                    estimate="instant",
                ),
                "capture_state_snapshot": _action(
                    _snapshot,
                    "Return a point-in-time body state snapshot.",
                    idempotent=True,
                    estimate="instant",
                ),
            },
        }

    _register_node(server, "connection", connection_node)

    def body_node() -> Descriptor:
        state = body.snapshot()
        return {
            "type": "context",
            "props": _section(state, "body"),
            "summary": "Body identity and capability summary.",
        }

    _register_node(server, "body", body_node)

    def pose_node() -> Descriptor:
        state = body.snapshot()
        pose = _section(state, "pose")
        actions: dict[str, Descriptor] = {}
        if _motion_can_run(state):
            actions["look_at_angles"] = _action(
                _look_at_angles,
                "Look at clamped pan and tilt angles.",
                params={
                    "pan": {
                        "type": "number",
                        "description": "Head pan target in degrees.",
                    },
                    "tilt": {
                        "type": "number",
                        "description": "Head tilt target in degrees.",
                    },
                },
                estimate="async",
            )
            actions["look_at_point"] = _action(
                _look_at_point,
                "Look toward a normalized point in body coordinates.",
                params={
                    "x": {
                        "type": "number",
                        "description": "Normalized left/right target from -1 to 1.",
                    },
                    "y": {
                        "type": "number",
                        "description": "Normalized down/up target from -1 to 1.",
                    },
                    "z": {
                        "type": "number",
                        "description": "Forward distance hint for the target.",
                    },
                },
                estimate="async",
            )
            actions["look_toward_sound"] = _action(
                _look_toward_sound,
                "Look toward the current audio direction of arrival.",
                estimate="async",
            )
        return {
            "type": "context",
            "props": pose,
            "summary": _pose_summary(pose),
            "actions": actions,
        }

    _register_node(server, "pose", pose_node)

    def motors_node() -> Descriptor:
        state = body.snapshot()
        return {
            "type": "status",
            "props": _section(state, "motors"),
            "summary": "Fake pan/tilt motor bus state.",
        }

    _register_node(server, "motors", motors_node)

    def media_node() -> Descriptor:
        state = body.snapshot()
        media = _section(state, "media")
        actions: dict[str, Descriptor] = {}
        if media["released"]:
            actions["acquire_media"] = _action(
                _acquire_media,
                "Acquire media devices for the body daemon.",
                estimate="fast",
            )
        else:
            actions["release_media"] = _action(
                _release_media,
                "Release media devices to another local process.",
                estimate="fast",
            )
        return {
            "type": "media",
            "props": media,
            "summary": f"Media owner: {media['owner']}.",
            "actions": actions,
        }

    _register_node(server, "media", media_node)

    def audio_node() -> Descriptor:
        state = body.snapshot()
        return {
            "type": "media",
            "props": _section(state, "audio"),
            "summary": "Audio input/output state.",
        }

    _register_node(server, "audio", audio_node)

    def vision_node() -> Descriptor:
        state = body.snapshot()
        actions: dict[str, Descriptor] = {}
        if not _section(state, "media")["released"]:
            actions["capture_frame"] = _action(
                _capture_frame,
                "Explicitly capture one camera frame.",
                estimate="fast",
            )
        return {
            "type": "media",
            "props": _section(state, "vision"),
            "summary": "Camera frame state and privacy mode.",
            "actions": actions,
        }

    _register_node(server, "vision", vision_node)

    def expression_node() -> Descriptor:
        state = body.snapshot()
        actions: dict[str, Descriptor] = {
            "sleep": _action(
                _sleep,
                "Move into a conservative sleep posture.",
                estimate="async",
            ),
            "gesture": _action(
                _gesture,
                "Run a named semantic body gesture.",
                params={
                    "name": {
                        "type": "string",
                        "enum": list(GESTURE_VALUES),
                        "description": "Gesture name.",
                    },
                },
                estimate="async",
            ),
            "set_idle_mode": _action(
                _set_idle_mode,
                "Set idle expression behavior.",
                params={
                    "mode": {
                        "type": "string",
                        "enum": list(IDLE_MODE_VALUES),
                        "description": "Idle mode.",
                    },
                },
                estimate="fast",
            ),
        }
        if not _section(state, "safety")["eStop"]:
            actions["wake"] = _action(
                _wake,
                "Move into an awake, attentive posture.",
                estimate="async",
            )
        return {
            "type": "context",
            "props": _section(state, "expression"),
            "summary": "Expression and gesture state.",
            "actions": actions,
        }

    _register_node(server, "expression", expression_node)

    def safety_node() -> Descriptor:
        state = body.snapshot()
        safety = _section(state, "safety")
        actions: dict[str, Descriptor] = {}
        if not safety["eStop"]:
            actions["emergency_stop"] = _action(
                _emergency_stop,
                "Immediately disable motion.",
                estimate="fast",
            )
        if safety["motionEnabled"]:
            actions["disable_motion"] = _action(
                _disable_motion,
                "Disable body motion.",
                estimate="fast",
            )
        elif not safety["eStop"]:
            actions["enable_motion"] = _action(
                _enable_motion,
                "Enable motion after safety checks.",
                dangerous=True,
                estimate="fast",
            )
        return {
            "type": "status",
            "props": safety,
            "summary": _safety_summary(safety),
            "actions": actions,
        }

    _register_node(server, "safety", safety_node)

    def tasks_node() -> Descriptor:
        state = body.snapshot()
        tasks = _section(state, "tasks")
        return {
            "type": "collection",
            "props": {"count": len(tasks)},
            "items": [_task_item(task) for task in tasks.values()],
            "summary": f"{len(tasks)} task(s) recorded.",
        }

    _register_node(server, "tasks", tasks_node)

    def calibration_node() -> Descriptor:
        state = body.snapshot()
        return {
            "type": "status",
            "props": _section(state, "calibration"),
            "summary": "Fake calibration defaults.",
        }

    _register_node(server, "calibration", calibration_node)

    def runtime_node() -> Descriptor:
        state = body.snapshot()
        return {
            "type": "status",
            "props": _section(state, "runtime"),
            "summary": "Provider runtime state.",
        }

    _register_node(server, "runtime", runtime_node)

    server.refresh()
    return server


def _action(
    handler: Handler,
    description: str,
    *,
    params: dict[str, Any] | None = None,
    dangerous: bool = False,
    idempotent: bool = False,
    estimate: str | None = None,
) -> Descriptor:
    action: Descriptor = {
        "handler": _wrap_handler(handler),
        "description": description,
    }
    if params is not None:
        action["params"] = params
    if dangerous:
        action["dangerous"] = True
    if idempotent:
        action["idempotent"] = True
    if estimate is not None:
        action["estimate"] = estimate
    return action


def _wrap_handler(handler: Handler) -> Callable[[dict[str, Any]], dict[str, Any]]:
    signature = inspect.signature(handler)
    parameter_names = list(signature.parameters)

    if not parameter_names:

        def wrapper_without_params(params: dict[str, Any]) -> dict[str, Any]:
            return handler()

        return wrapper_without_params

    def wrapper_with_params(params: dict[str, Any]) -> dict[str, Any]:
        kwargs = {name: params[name] for name in parameter_names if name in params}
        return handler(**kwargs)

    return wrapper_with_params


def _register_node(
    server: SlopServer,
    path: str,
    node_fn: Callable[[], Descriptor],
) -> None:
    cast(Any, server).node(path)(node_fn)


def _section(state: dict[str, Any], name: str) -> dict[str, Any]:
    return cast(dict[str, Any], state[name])


def _motion_can_run(state: dict[str, Any]) -> bool:
    safety = _section(state, "safety")
    return bool(safety["motionEnabled"]) and not bool(safety["eStop"])


def _raise_if_motion_blocked(body: BodyBackend) -> None:
    if not _motion_can_run(body.snapshot()):
        raise SlopConflictError("motion is disabled or emergency-stopped")


def _raise_if_estopped(body: BodyBackend) -> None:
    if _section(body.snapshot(), "safety")["eStop"]:
        raise SlopConflictError("emergency stop is active")


def _task_result(task: TaskState) -> dict[str, Any]:
    return {
        "taskId": task.task_id,
        "task": task.to_dict(),
    }


def _async_task(task: TaskState) -> dict[str, Any]:
    data = _task_result(task)
    data["__async"] = True
    return data


def _task_item(task: Any) -> Descriptor:
    task_dict = cast(dict[str, Any], task)
    return {
        "id": str(task_dict["taskId"]),
        "props": task_dict,
        "summary": f"{task_dict['name']} is {task_dict['status']}.",
    }


def _pose_summary(pose: dict[str, Any]) -> str:
    head = cast(dict[str, Any], pose["head"])
    return f"Head pan {head['pan']} degrees, tilt {head['tilt']} degrees."


def _safety_summary(safety: dict[str, Any]) -> str:
    if safety["eStop"]:
        return "Emergency stop is active; motion is disabled."
    if safety["motionEnabled"]:
        return "Motion is enabled with conservative fake limits."
    return "Motion is disabled."


def _coerce_idle_mode(value: str) -> IdleMode:
    if value not in IDLE_MODE_VALUES:
        msg = f"unsupported idle mode: {value}"
        raise ValueError(msg)
    return value
