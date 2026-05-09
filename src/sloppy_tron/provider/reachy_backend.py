"""Reachy Mini daemon backend for the SLOP body provider.

This adapter intentionally talks to the Reachy Mini daemon's public FastAPI
surface instead of importing the upstream SDK. That keeps SloppyTron lightweight:
from the consumer's point of view the body state tree is the same whether the
physical/simulated body behind the provider is fake, ROS 2, or Reachy's MuJoCo
backend.
"""

from __future__ import annotations

import copy
import json
import math
from collections.abc import Mapping
from itertools import count
from time import time
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sloppy_tron.provider.contract import BodyGesture, IdleMode, JsonObject
from sloppy_tron.provider.state import ProviderState, TaskState


class ReachyDaemonClient(Protocol):
    """Minimal HTTP client used by :class:`ReachyDaemonBackend`."""

    def get_json(self, path: str) -> object: ...

    def post_json(self, path: str, payload: JsonObject | None = None) -> object: ...


class HttpReachyDaemonClient:
    """Small stdlib JSON client for a running Reachy Mini daemon."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        *,
        timeout: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def get_json(self, path: str) -> object:
        return self._request_json("GET", path)

    def post_json(self, path: str, payload: JsonObject | None = None) -> object:
        return self._request_json("POST", path, payload)

    def _request_json(
        self,
        method: str,
        path: str,
        payload: JsonObject | None = None,
    ) -> object:
        url = f"http://{self.host}:{self.port}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            message = f"{method} {path} failed: HTTP {exc.code} {detail}"
            raise ConnectionError(message) from exc
        except (OSError, TimeoutError, URLError) as exc:
            raise ConnectionError(f"{method} {path} failed: {exc}") from exc
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ConnectionError(f"{method} {path} returned invalid JSON") from exc


class ReachyDaemonBackend:
    """Body backend backed by the Reachy Mini daemon.

    Works with both upstream daemon modes:
    - ``reachy-mini-daemon --mockup-sim`` for lightweight CI/local testing
    - ``reachy-mini-daemon --sim --headless`` for MuJoCo simulation
    """

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8000,
        client: ReachyDaemonClient | None = None,
        motion_duration: float = 0.5,
    ) -> None:
        self._host = host
        self._port = port
        self._client = client or HttpReachyDaemonClient(host, port)
        self._motion_duration = motion_duration
        self._state = ProviderState()
        self._task_numbers = count(1)
        self._daemon_status: JsonObject = {}
        self._full_state: JsonObject = {}
        self._media_status: JsonObject = {}
        self._errors: list[str] = []

    def snapshot(self) -> JsonObject:
        self._refresh_from_daemon()
        return copy.deepcopy(self._provider_state())

    def wake(self) -> TaskState:
        task = self._post_async_move(
            "wake",
            "/api/move/play/wake_up",
            {"posture": "awake"},
        )
        if task.status != "failed":
            self._state.motion_enabled = True
            self._state.microphone_muted = False
            self._state.expression = "awake"
            self._state.idle_mode = "attentive"
        return task

    def sleep(self) -> TaskState:
        task = self._post_async_move(
            "sleep",
            "/api/move/play/goto_sleep",
            {"posture": "sleep"},
        )
        if task.status != "failed":
            self._state.expression = "sleep"
            self._state.idle_mode = "off"
        return task

    def look_at_angles(self, pan: float, tilt: float) -> TaskState:
        clamped_pan = self._state.pan_limits.clamp(pan)
        clamped_tilt = self._state.tilt_limits.clamp(tilt)
        if not self._motion_can_run():
            return self._complete_task(
                "look_at_angles",
                {"pan": pan, "tilt": tilt},
                {"accepted": False, "pan": clamped_pan, "tilt": clamped_tilt},
            )
        payload = _goto_payload_for_angles(
            clamped_pan,
            clamped_tilt,
            duration=self._motion_duration,
        )
        task = self._post_async_move(
            "look_at_angles",
            "/api/move/goto",
            {"pan": clamped_pan, "tilt": clamped_tilt},
            payload=payload,
            result_base={
                "accepted": True,
                "pan": clamped_pan,
                "tilt": clamped_tilt,
            },
        )
        if task.status != "failed":
            self._state.head.pan = clamped_pan
            self._state.head.tilt = clamped_tilt
        return task

    def look_at_point(self, x: float, y: float, z: float) -> TaskState:
        pan, tilt = _angles_from_point(x, y, z)
        clamped_pan = self._state.pan_limits.clamp(pan)
        clamped_tilt = self._state.tilt_limits.clamp(tilt)
        if not self._motion_can_run():
            return self._complete_task(
                "look_at_point",
                {"x": x, "y": y, "z": z},
                {"accepted": False, "pan": clamped_pan, "tilt": clamped_tilt},
            )
        payload = _goto_payload_for_angles(
            clamped_pan,
            clamped_tilt,
            duration=self._motion_duration,
        )
        task = self._post_async_move(
            "look_at_point",
            "/api/move/goto",
            {"x": x, "y": y, "z": z},
            payload=payload,
            result_base={
                "accepted": True,
                "pan": clamped_pan,
                "tilt": clamped_tilt,
            },
        )
        if task.status != "failed":
            self._state.head.pan = clamped_pan
            self._state.head.tilt = clamped_tilt
        return task

    def look_toward_sound(self) -> TaskState:
        doa = _object_or_empty(self._full_state.get("doa"))
        angle = _number(doa.get("angle"), 0.0)
        # Upstream DoA convention: 0=left, pi/2=front, pi=right.
        pan = math.degrees((math.pi / 2) - angle)
        task = self.look_at_angles(pan=pan, tilt=0.0)
        task.name = "look_toward_sound"
        task.target = {"directionOfArrival": angle if doa else None}
        self._state.tasks[task.task_id] = task
        return task

    def gesture(self, gesture: BodyGesture) -> TaskState:
        if gesture == "wake":
            return self.wake()
        if gesture == "sleep":
            return self.sleep()
        self._state.expression = gesture
        return self._complete_task("gesture", {"gesture": gesture})

    def capture_frame(self) -> TaskState:
        media = self._media_state()
        captured = bool(_object_or_empty(media.get("camera")).get("enabled", False))
        self._state.frame_available = captured
        self._state.last_frame_summary = (
            "reachy daemon frame available" if captured else "media unavailable"
        )
        return self._complete_task(
            "capture_frame",
            {"privacyMode": self._state.privacy_mode},
            {"captured": captured},
        )

    def set_idle_mode(self, idle_mode: IdleMode) -> TaskState:
        self._state.idle_mode = idle_mode
        return self._complete_task("set_idle_mode", {"idleMode": idle_mode})

    def release_media(self) -> TaskState:
        return self._post_sync(
            "release_media",
            "/api/media/release",
            {},
            {"released": True},
        )

    def acquire_media(self) -> TaskState:
        return self._post_sync(
            "acquire_media",
            "/api/media/acquire",
            {},
            {"released": False},
        )

    def enable_motion(self) -> TaskState:
        task = self._post_sync(
            "enable_motion",
            "/api/motors/set_mode/enabled",
            {},
            {"accepted": True},
        )
        if task.status != "failed":
            self._state.motion_enabled = True
        return task

    def disable_motion(self) -> TaskState:
        task = self._post_sync(
            "disable_motion",
            "/api/motors/set_mode/disabled",
            {},
            {"accepted": True},
        )
        if task.status != "failed":
            self._state.motion_enabled = False
        return task

    def emergency_stop(self) -> TaskState:
        try:
            self._client.post_json("/api/motors/set_mode/disabled")
        except ConnectionError as exc:
            self._errors = [str(exc)]
            self._state.motion_enabled = False
            self._state.emergency_stopped = True
            self._state.expression = "emergency_stop"
            return self._failed_task("emergency_stop", {}, exc)
        self._state.motion_enabled = False
        self._state.emergency_stopped = True
        self._state.expression = "emergency_stop"
        return self._complete_task("emergency_stop", {}, {"accepted": True})

    def _refresh_from_daemon(self) -> None:
        errors: list[str] = []
        self._daemon_status = self._try_get(
            "/api/daemon/status",
            self._daemon_status,
            errors,
        )
        self._full_state = self._try_get(
            "/api/state/full?with_head_joints=true&with_doa=true",
            self._full_state,
            errors,
        )
        self._media_status = self._try_get(
            "/api/media/status",
            self._media_status,
            errors,
        )
        self._errors = errors
        self._state.motion_enabled = self._motor_mode() == "enabled"
        self._state.last_seen_at = time()

    def _try_get(
        self,
        path: str,
        previous: JsonObject,
        errors: list[str],
    ) -> JsonObject:
        try:
            value = self._client.get_json(path)
        except ConnectionError as exc:
            errors.append(str(exc))
            return previous
        return _object_or_empty(value)

    def _post_sync(
        self,
        name: str,
        path: str,
        target: JsonObject,
        result: JsonObject,
    ) -> TaskState:
        try:
            self._client.post_json(path)
        except ConnectionError as exc:
            self._errors = [str(exc)]
            return self._failed_task(name, target, exc)
        self._errors = []
        if name == "release_media":
            self._state.media_released = True
        elif name == "acquire_media":
            self._state.media_released = False
        return self._complete_task(name, target, result)

    def _post_async_move(
        self,
        name: str,
        path: str,
        target: JsonObject,
        *,
        payload: JsonObject | None = None,
        result_base: JsonObject | None = None,
    ) -> TaskState:
        try:
            response = self._client.post_json(path, payload)
        except ConnectionError as exc:
            self._errors = [str(exc)]
            return self._failed_task(name, target, exc)
        self._errors = []
        result = {} if result_base is None else copy.deepcopy(result_base)
        result["externalTaskId"] = _external_task_id(response)
        return self._complete_task(name, target, result, async_task=True)

    def _provider_state(self) -> JsonObject:
        state = self._state.to_dict()
        state["connection"] = self._connection_state()
        state["body"] = self._body_state()
        state["pose"] = self._pose_state()
        state["motors"] = self._motors_state()
        state["media"] = self._media_state()
        state["audio"] = self._audio_state()
        state["vision"] = self._vision_state()
        state["safety"] = self._safety_state()
        state["calibration"] = self._calibration_state()
        state["runtime"] = self._runtime_state()
        return state

    def _connection_state(self) -> JsonObject:
        daemon_state = _string(self._daemon_status.get("state"), "unknown")
        ok = daemon_state == "running" and not self._errors
        errors = list(self._errors)
        status_error = _string(self._daemon_status.get("error"), "")
        if status_error:
            errors.append(status_error)
        return cast(
            JsonObject,
            {
                "status": "ok" if ok else "degraded",
                "host": self._host,
                "port": self._port,
                "daemonVersion": _string(self._daemon_status.get("version"), "unknown"),
                "backend": "reachy_daemon",
                "bodyBackend": self._body_backend(),
                "lastSeenAt": self._state.last_seen_at,
                "errors": errors,
            },
        )

    def _body_state(self) -> JsonObject:
        return cast(
            JsonObject,
            {
                "name": "Reachy Mini",
                "model": "reachy-mini-sim"
                if self._body_backend() in {"mujoco", "mockup_sim"}
                else "reachy-mini",
                "coordinateFrame": (
                    "reachy_head_pose_radians_synthetic_pan_tilt_degrees"
                ),
                "capabilities": [
                    "wake",
                    "sleep",
                    "look_at_angles",
                    "look_at_point",
                    "gesture",
                    "capture_frame",
                    "safety_state",
                    "body_yaw",
                    "antennas",
                ],
            },
        )

    def _pose_state(self) -> JsonObject:
        head = self._head_state()
        antennas = self._antenna_state()
        return cast(
            JsonObject,
            {
                "head": head,
                "bodyYaw": self._body_yaw_degrees(),
                "antennas": antennas,
                "target": head,
                "rawHeadPose": _object_or_empty(self._full_state.get("head_pose")),
                "limits": {
                    "pan": self._state.pan_limits.to_dict(),
                    "tilt": self._state.tilt_limits.to_dict(),
                },
                "moving": False,
            },
        )

    def _motors_state(self) -> JsonObject:
        mode = self._motor_mode()
        backend_status = _object_or_empty(self._daemon_status.get("backend_status"))
        fault = _string(backend_status.get("error"), "")
        faults = [fault] if fault else []
        if self._state.emergency_stopped:
            faults.append("emergency_stop")
        return cast(
            JsonObject,
            {
                "mode": mode,
                "bus": "reachy_daemon",
                "devices": [
                    {"name": "body_rotation", "kind": "dynamixel"},
                    {"name": "stewart_1", "kind": "dynamixel"},
                    {"name": "stewart_2", "kind": "dynamixel"},
                    {"name": "stewart_3", "kind": "dynamixel"},
                    {"name": "stewart_4", "kind": "dynamixel"},
                    {"name": "stewart_5", "kind": "dynamixel"},
                    {"name": "stewart_6", "kind": "dynamixel"},
                    {"name": "left_antenna", "kind": "dynamixel"},
                    {"name": "right_antenna", "kind": "dynamixel"},
                ],
                "faults": faults,
                "temperatures": {},
                "voltage": None,
            },
        )

    def _media_state(self) -> JsonObject:
        available = _bool(self._media_status.get("available"), False)
        no_media = _bool(self._media_status.get("no_media"), False)
        released = _bool(
            self._media_status.get("released"),
            self._state.media_released,
        )
        enabled = available and not released and not no_media
        return cast(
            JsonObject,
            {
                "camera": {"available": available, "enabled": enabled},
                "microphone": {
                    "available": available,
                    "enabled": enabled,
                    "muted": no_media or self._state.microphone_muted,
                },
                "speaker": {
                    "available": not no_media,
                    "enabled": not no_media and not released,
                    "muted": self._state.speaker_muted,
                },
                "owner": "released" if released else "body_daemon",
                "released": released,
                "muted": no_media or self._state.microphone_muted,
                "noMedia": no_media,
            },
        )

    def _audio_state(self) -> JsonObject:
        doa = _object_or_empty(self._full_state.get("doa"))
        return cast(
            JsonObject,
            {
                "directionOfArrival": doa.get("angle"),
                "speechDetected": _bool(doa.get("speech_detected"), False),
                "inputLevel": 0.0,
                "outputLevel": 0.0,
            },
        )

    def _vision_state(self) -> JsonObject:
        media = self._media_state()
        camera = _object_or_empty(media.get("camera"))
        return cast(
            JsonObject,
            {
                "frameAvailable": self._state.frame_available,
                "lastFrameSummary": self._state.last_frame_summary,
                "privacyMode": self._state.privacy_mode,
                "cameraSpecs": _string(
                    self._daemon_status.get("camera_specs_name"),
                    "",
                ),
                "streamAvailable": _bool(camera.get("enabled"), False),
            },
        )

    def _safety_state(self) -> JsonObject:
        return cast(
            JsonObject,
            {
                "motionEnabled": self._motor_mode() == "enabled"
                and not self._state.emergency_stopped,
                "eStop": self._state.emergency_stopped,
                "watchdog": "expired" if self._errors else "ok",
                "maxSpeed": "slow",
                "maxAmplitude": {
                    "pan": self._state.pan_limits.maximum,
                    "tilt": self._state.tilt_limits.maximum,
                },
                "privacy": {
                    "camera": "explicit_capture_only",
                    "microphone": "muted"
                    if _bool(self._media_status.get("no_media"), False)
                    or self._state.microphone_muted
                    else "available",
                    "speaker": "available"
                    if not self._state.speaker_muted
                    else "muted",
                    "remoteAccess": "daemon_localhost_only",
                },
            },
        )

    def _calibration_state(self) -> JsonObject:
        return cast(
            JsonObject,
            {
                "status": "reachy_daemon",
                "centers": {"pan": 0.0, "tilt": 0.0},
                "limits": {
                    "pan": self._state.pan_limits.to_dict(),
                    "tilt": self._state.tilt_limits.to_dict(),
                },
                "requiredSteps": [],
            },
        )

    def _runtime_state(self) -> JsonObject:
        return cast(
            JsonObject,
            {
                "uptime": max(0.0, time() - self._state.started_at),
                "logsSummary": "reachy daemon backend ready"
                if not self._errors
                else "; ".join(self._errors),
                "config": {
                    "backend": "reachy_daemon",
                    "providerBackend": "reachy_daemon",
                    "bodyBackend": self._body_backend(),
                    "simulationMode": self._body_backend(),
                    "host": self._host,
                    "port": self._port,
                },
            },
        )

    def _head_state(self) -> JsonObject:
        head_pose = _object_or_empty(self._full_state.get("head_pose"))
        yaw = _number(head_pose.get("yaw"), math.radians(self._state.head.pan))
        pitch = _number(head_pose.get("pitch"), math.radians(self._state.head.tilt))
        return {"pan": math.degrees(yaw), "tilt": math.degrees(pitch)}

    def _antenna_state(self) -> JsonObject:
        antennas = _list_or_empty(self._full_state.get("antennas_position"))
        if len(antennas) < 2:
            return {}
        return {
            "left": math.degrees(_number(antennas[0], 0.0)),
            "right": math.degrees(_number(antennas[1], 0.0)),
        }

    def _body_yaw_degrees(self) -> float | None:
        body_yaw = self._full_state.get("body_yaw")
        if isinstance(body_yaw, int | float):
            return math.degrees(float(body_yaw))
        return None

    def _motor_mode(self) -> str:
        mode = _string(self._full_state.get("control_mode"), "")
        if mode:
            return mode
        backend_status = _object_or_empty(self._daemon_status.get("backend_status"))
        return _string(backend_status.get("motor_control_mode"), "disabled")

    def _body_backend(self) -> str:
        if _bool(self._daemon_status.get("simulation_enabled"), False):
            return "mujoco"
        if _bool(self._daemon_status.get("mockup_sim_enabled"), False):
            return "mockup_sim"
        return "robot"

    def _motion_can_run(self) -> bool:
        self._refresh_from_daemon()
        return self._motor_mode() == "enabled" and not self._state.emergency_stopped

    def _complete_task(
        self,
        name: str,
        target: JsonObject,
        result: JsonObject | None = None,
        *,
        async_task: bool = False,
    ) -> TaskState:
        now = time()
        task = TaskState(
            task_id=f"reachy-task-{next(self._task_numbers)}",
            name=name,
            status="accepted" if async_task else "succeeded",
            progress=0.0 if async_task else 1.0,
            target=target,
            started_at=now,
            completed_at=None if async_task else now,
            result={} if result is None else result,
        )
        self._state.tasks[task.task_id] = task
        self._state.last_seen_at = now
        return task

    def _failed_task(
        self,
        name: str,
        target: JsonObject,
        error: BaseException,
    ) -> TaskState:
        now = time()
        task = TaskState(
            task_id=f"reachy-task-{next(self._task_numbers)}",
            name=name,
            status="failed",
            progress=1.0,
            target=target,
            started_at=now,
            completed_at=now,
            result={"accepted": False, "error": str(error)},
        )
        self._state.tasks[task.task_id] = task
        self._state.last_seen_at = now
        return task


def _goto_payload_for_angles(pan: float, tilt: float, *, duration: float) -> JsonObject:
    return cast(
        JsonObject,
        {
            "head_pose": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "roll": 0.0,
                "pitch": math.radians(tilt),
                "yaw": math.radians(pan),
            },
            "duration": duration,
            "interpolation": "minjerk",
        },
    )


def _angles_from_point(x: float, y: float, z: float) -> tuple[float, float]:
    horizontal = math.hypot(x, y)
    if horizontal == 0.0 and z == 0.0:
        return 0.0, 0.0
    pan = math.degrees(math.atan2(y, x)) if horizontal else 0.0
    tilt = math.degrees(math.atan2(z, horizontal))
    return pan, tilt


def _external_task_id(response: object) -> str | None:
    data = _object_or_empty(response)
    external = data.get("uuid") or data.get("taskId") or data.get("job_id")
    if isinstance(external, str) and external:
        return external
    return None


def _object_or_empty(value: object) -> JsonObject:
    if isinstance(value, Mapping):
        return cast(JsonObject, dict(value))
    return {}


def _list_or_empty(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _number(value: object, default: float) -> float:
    if isinstance(value, int | float):
        return float(value)
    return default


def _string(value: object, default: str) -> str:
    if isinstance(value, str):
        return value
    return default


def _bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default
