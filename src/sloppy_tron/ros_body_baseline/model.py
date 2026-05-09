"""Pure-Python kinematic body model used by the ROS baseline node."""

from __future__ import annotations

import copy
from time import time
from typing import cast

from sloppy_tron.provider.contract import BodyGesture, IdleMode, JsonObject, TaskStatus
from sloppy_tron.provider.state import ProviderState, TaskState, coerce_gesture

JOINT_NAMES: tuple[str, ...] = (
    "body_yaw_joint",
    "head_pan_joint",
    "head_tilt_joint",
    "antenna_left_joint",
    "antenna_right_joint",
)


class BaselineBodyModel:
    """Deterministic Reachy-like kinematic baseline for the ROS body graph.

    This model intentionally does not simulate physics. It mirrors the
    SLOP-visible body state and command semantics needed by the ROS bridge so it
    can become the baseline for SloppyTron's own body graph.
    """

    def __init__(self) -> None:
        self._state = ProviderState()
        self._body_yaw = 0.0
        self._antenna_left = 0.0
        self._antenna_right = 0.0

    def snapshot(self) -> JsonObject:
        """Return a copy of the current body-provider state tree."""

        state = copy.deepcopy(self._state.to_dict())
        self._annotate_connection(state)
        self._annotate_body(state)
        self._annotate_pose(state)
        self._annotate_motors(state)
        self._annotate_calibration(state)
        self._annotate_runtime(state)
        return state

    def joint_positions(self) -> dict[str, float]:
        """Return deterministic joint positions in degrees for ROS JointState."""

        return {
            "body_yaw_joint": self._body_yaw,
            "head_pan_joint": self._state.head.pan,
            "head_tilt_joint": self._state.head.tilt,
            "antenna_left_joint": self._antenna_left,
            "antenna_right_joint": self._antenna_right,
        }

    def apply_command(
        self,
        action: str,
        params: JsonObject,
        *,
        task_id: str,
    ) -> TaskState:
        """Apply a bridge command and preserve the bridge task id."""

        if action == "wake":
            return self.wake(task_id=task_id)
        if action == "sleep":
            return self.sleep(task_id=task_id)
        if action == "look_at_angles":
            return self.look_at_angles(
                _number(params, "pan"),
                _number(params, "tilt"),
                task_id=task_id,
            )
        if action == "look_at_point":
            return self.look_at_point(
                _number(params, "x"),
                _number(params, "y"),
                _number(params, "z"),
                task_id=task_id,
            )
        if action == "look_toward_sound":
            return self.look_toward_sound(task_id=task_id)
        if action == "gesture":
            return self.gesture(_command_gesture(params), task_id=task_id)
        if action == "capture_frame":
            return self.capture_frame(task_id=task_id)
        if action == "set_idle_mode":
            return self.set_idle_mode(_command_idle_mode(params), task_id=task_id)
        if action == "release_media":
            return self.release_media(task_id=task_id)
        if action == "acquire_media":
            return self.acquire_media(task_id=task_id)
        if action == "enable_motion":
            return self.enable_motion(task_id=task_id)
        if action == "disable_motion":
            return self.disable_motion(task_id=task_id)
        if action == "emergency_stop":
            return self.emergency_stop(task_id=task_id)
        msg = f"unsupported body command action: {action}"
        raise ValueError(msg)

    def wake(self, *, task_id: str) -> TaskState:
        self._state.motion_enabled = True
        self._state.microphone_muted = False
        self._state.expression = "awake"
        self._state.idle_mode = "attentive"
        return self._complete("wake", {"posture": "awake"}, task_id=task_id)

    def sleep(self, *, task_id: str) -> TaskState:
        self._state.motion_enabled = False
        self._state.microphone_muted = True
        self._state.expression = "sleep"
        self._state.idle_mode = "off"
        self._state.head.pan = 0.0
        self._state.head.tilt = 0.0
        self._body_yaw = 0.0
        self._antenna_left = 0.0
        self._antenna_right = 0.0
        return self._complete("sleep", {"posture": "sleep"}, task_id=task_id)

    def look_at_angles(self, pan: float, tilt: float, *, task_id: str) -> TaskState:
        clamped_pan = self._state.pan_limits.clamp(pan)
        clamped_tilt = self._state.tilt_limits.clamp(tilt)
        if not self._motion_can_run():
            return self._complete(
                "look_at_angles",
                {"pan": pan, "tilt": tilt},
                {"accepted": False, "reason": "motion_disabled"},
                task_id=task_id,
                status="failed",
            )
        self._state.head.pan = clamped_pan
        self._state.head.tilt = clamped_tilt
        return self._complete(
            "look_at_angles",
            {"pan": pan, "tilt": tilt},
            {"accepted": True, "pan": clamped_pan, "tilt": clamped_tilt},
            task_id=task_id,
        )

    def look_at_point(
        self,
        x: float,
        y: float,
        z: float,
        *,
        task_id: str,
    ) -> TaskState:
        pan = self._state.pan_limits.clamp(x * self._state.pan_limits.maximum)
        tilt = self._state.tilt_limits.clamp(y * self._state.tilt_limits.maximum)
        task = self.look_at_angles(pan, tilt, task_id=task_id)
        task.name = "look_at_point"
        task.target = {"x": x, "y": y, "z": z}
        self._state.tasks[task.task_id] = task
        return task

    def look_toward_sound(self, *, task_id: str) -> TaskState:
        task = self.look_at_angles(0.0, 0.0, task_id=task_id)
        task.name = "look_toward_sound"
        task.target = {"directionOfArrival": None}
        self._state.tasks[task.task_id] = task
        return task

    def gesture(self, gesture: BodyGesture, *, task_id: str) -> TaskState:
        if gesture == "wake":
            return self.wake(task_id=task_id)
        if gesture == "sleep":
            return self.sleep(task_id=task_id)
        if gesture == "curious_tilt" and self._motion_can_run():
            self._state.head.pan = 0.0
            self._state.head.tilt = 12.0
            self._antenna_left = 18.0
            self._antenna_right = -18.0
        elif gesture == "look_away" and self._motion_can_run():
            self._state.head.pan = -35.0
            self._state.head.tilt = 0.0
        elif gesture == "look_back" and self._motion_can_run():
            self._state.head.pan = 0.0
            self._state.head.tilt = 0.0
        elif gesture == "nod" and self._motion_can_run():
            self._state.head.tilt = 8.0
        elif gesture == "shake_no" and self._motion_can_run():
            self._state.head.pan = 18.0
        elif gesture == "small_ack" and self._motion_can_run():
            self._state.head.tilt = 5.0
        self._state.expression = gesture
        return self._complete("gesture", {"gesture": gesture}, task_id=task_id)

    def capture_frame(self, *, task_id: str) -> TaskState:
        captured = not self._state.media_released
        self._state.frame_available = captured
        self._state.last_frame_summary = (
            "baseline frame captured" if captured else "media released"
        )
        return self._complete(
            "capture_frame",
            {"privacyMode": self._state.privacy_mode},
            {"captured": captured},
            task_id=task_id,
        )

    def set_idle_mode(self, idle_mode: IdleMode, *, task_id: str) -> TaskState:
        self._state.idle_mode = idle_mode
        return self._complete("set_idle_mode", {"idleMode": idle_mode}, task_id=task_id)

    def release_media(self, *, task_id: str) -> TaskState:
        self._state.media_released = True
        return self._complete("release_media", {}, {"released": True}, task_id=task_id)

    def acquire_media(self, *, task_id: str) -> TaskState:
        self._state.media_released = False
        return self._complete("acquire_media", {}, {"released": False}, task_id=task_id)

    def enable_motion(self, *, task_id: str) -> TaskState:
        accepted = not self._state.emergency_stopped
        self._state.motion_enabled = accepted
        return self._complete(
            "enable_motion",
            {},
            {"accepted": accepted},
            task_id=task_id,
            status="succeeded" if accepted else "failed",
        )

    def disable_motion(self, *, task_id: str) -> TaskState:
        self._state.motion_enabled = False
        return self._complete("disable_motion", {}, {"accepted": True}, task_id=task_id)

    def emergency_stop(self, *, task_id: str) -> TaskState:
        self._state.motion_enabled = False
        self._state.emergency_stopped = True
        self._state.expression = "emergency_stop"
        return self._complete("emergency_stop", {}, {"accepted": True}, task_id=task_id)

    def _motion_can_run(self) -> bool:
        return self._state.motion_enabled and not self._state.emergency_stopped

    def _complete(
        self,
        name: str,
        target: JsonObject,
        result: JsonObject | None = None,
        *,
        task_id: str,
        status: TaskStatus = "succeeded",
    ) -> TaskState:
        now = time()
        task = TaskState(
            task_id=task_id,
            name=name,
            status=status,
            progress=1.0,
            target=target,
            started_at=now,
            completed_at=now,
            result={} if result is None else result,
        )
        self._state.tasks[task_id] = task
        self._state.last_seen_at = now
        return task

    def _annotate_connection(self, state: JsonObject) -> None:
        connection = _object_section(state, "connection")
        connection.update(
            {
                "status": "degraded"
                if self._state.emergency_stopped or not self._state.watchdog_ok
                else "ok",
                "host": "ros_graph",
                "daemonVersion": "0.0.0",
                "backend": "ros_baseline",
                "bodyBackend": "ros_baseline",
                "lastSeenAt": self._state.last_seen_at,
                "errors": [],
            }
        )

    def _annotate_body(self, state: JsonObject) -> None:
        state["body"] = {
            "name": "SloppyTron ROS Baseline",
            "model": "reachy-compatible-kinematic-baseline",
            "coordinateFrame": "head_pan_tilt_degrees_body_yaw_degrees",
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
        }

    def _annotate_pose(self, state: JsonObject) -> None:
        pose = _object_section(state, "pose")
        head = self._state.head.to_dict()
        pose.update(
            {
                "head": head,
                "bodyYaw": self._body_yaw,
                "antennas": {
                    "left": self._antenna_left,
                    "right": self._antenna_right,
                },
                "target": head,
                "limits": {
                    "pan": self._state.pan_limits.to_dict(),
                    "tilt": self._state.tilt_limits.to_dict(),
                    "bodyYaw": {"min": -180.0, "max": 180.0},
                    "antennas": {"min": -90.0, "max": 90.0},
                },
                "moving": False,
            }
        )

    def _annotate_motors(self, state: JsonObject) -> None:
        state["motors"] = {
            "mode": "enabled" if self._state.motion_enabled else "disabled",
            "bus": "ros_baseline",
            "devices": [
                {"name": "body_yaw", "kind": "kinematic_joint"},
                {"name": "head_pan", "kind": "kinematic_joint"},
                {"name": "head_tilt", "kind": "kinematic_joint"},
                {"name": "antenna_left", "kind": "kinematic_joint"},
                {"name": "antenna_right", "kind": "kinematic_joint"},
            ],
            "faults": ["emergency_stop"] if self._state.emergency_stopped else [],
            "temperatures": {},
            "voltage": None,
        }

    def _annotate_calibration(self, state: JsonObject) -> None:
        state["calibration"] = {
            "status": "ros_baseline_defaults",
            "centers": {
                "bodyYaw": 0.0,
                "pan": 0.0,
                "tilt": 0.0,
                "antennaLeft": 0.0,
                "antennaRight": 0.0,
            },
            "limits": _object_section(_object_section(state, "pose"), "limits"),
            "requiredSteps": [],
        }

    def _annotate_runtime(self, state: JsonObject) -> None:
        runtime = _object_section(state, "runtime")
        runtime.update(
            {
                "uptime": max(0.0, time() - self._state.started_at),
                "logsSummary": "ROS kinematic baseline ready",
                "config": {
                    "backend": "ros_baseline",
                    "bodyModel": "reachy_compatible_kinematic_baseline",
                    "physics": "none",
                },
            }
        )


def _object_section(data: JsonObject, name: str) -> JsonObject:
    section = data.get(name)
    if isinstance(section, dict):
        return section
    section = {}
    data[name] = section
    return section


def _number(data: JsonObject, name: str) -> float:
    value = data.get(name)
    if isinstance(value, int | float):
        return float(value)
    msg = f"{name} must be numeric"
    raise ValueError(msg)


def _command_gesture(params: JsonObject) -> BodyGesture:
    value = params.get("gesture", params.get("name"))
    if not isinstance(value, str):
        raise ValueError("gesture command requires gesture/name string")
    return coerce_gesture(value)


def _command_idle_mode(params: JsonObject) -> IdleMode:
    value = params.get("idleMode", params.get("mode"))
    if value not in {"off", "breathing", "attentive"}:
        raise ValueError(f"unsupported idle mode: {value}")
    return cast(IdleMode, value)
