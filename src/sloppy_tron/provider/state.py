"""Typed state tree for the SloppyTron body provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time

from sloppy_tron.provider.contract import (
    BodyGesture,
    IdleMode,
    JsonObject,
    JsonValue,
    TaskStatus,
)


@dataclass(slots=True)
class AngleLimits:
    minimum: float
    maximum: float

    def clamp(self, value: float) -> float:
        return min(max(value, self.minimum), self.maximum)

    def to_dict(self) -> JsonObject:
        return {"min": self.minimum, "max": self.maximum}


@dataclass(slots=True)
class HeadPose:
    pan: float = 0.0
    tilt: float = 0.0

    def to_dict(self) -> JsonObject:
        return {"pan": self.pan, "tilt": self.tilt}


@dataclass(slots=True)
class TaskState:
    task_id: str
    name: str
    status: TaskStatus
    progress: float
    target: JsonObject
    started_at: float
    completed_at: float | None = None
    result: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "taskId": self.task_id,
            "name": self.name,
            "status": self.status,
            "progress": self.progress,
            "target": self.target,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "result": self.result,
            "cancelAffordance": "cancel_task",
        }


@dataclass(slots=True)
class ProviderState:
    started_at: float = field(default_factory=time)
    last_seen_at: float = field(default_factory=time)
    head: HeadPose = field(default_factory=HeadPose)
    pan_limits: AngleLimits = field(default_factory=lambda: AngleLimits(-60.0, 60.0))
    tilt_limits: AngleLimits = field(default_factory=lambda: AngleLimits(-35.0, 35.0))
    motion_enabled: bool = False
    emergency_stopped: bool = False
    watchdog_ok: bool = True
    idle_mode: IdleMode = "off"
    expression: str = "sleep"
    media_released: bool = False
    microphone_muted: bool = True
    speaker_muted: bool = False
    privacy_mode: str = "local_explicit_capture_only"
    frame_available: bool = False
    last_frame_summary: str | None = None
    tasks: dict[str, TaskState] = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "connection": self._connection_state(),
            "body": self._body_state(),
            "pose": self._pose_state(),
            "motors": self._motors_state(),
            "media": self._media_state(),
            "audio": self._audio_state(),
            "vision": self._vision_state(),
            "expression": self._expression_state(),
            "safety": self._safety_state(),
            "tasks": self._tasks_state(),
            "calibration": self._calibration_state(),
            "runtime": self._runtime_state(),
        }

    def _connection_state(self) -> JsonObject:
        status = "degraded" if self.emergency_stopped or not self.watchdog_ok else "ok"
        return {
            "status": status,
            "host": "localhost",
            "daemonVersion": "0.0.0",
            "backend": "fake",
            "lastSeenAt": self.last_seen_at,
            "errors": [],
        }

    def _body_state(self) -> JsonObject:
        return {
            "name": "SloppyTron",
            "model": "v0-dev-rig",
            "coordinateFrame": "head_pan_tilt_degrees",
            "capabilities": [
                "wake",
                "sleep",
                "look_at_angles",
                "gesture",
                "capture_frame",
                "safety_state",
            ],
        }

    def _pose_state(self) -> JsonObject:
        return {
            "head": self.head.to_dict(),
            "bodyYaw": None,
            "antennas": {},
            "target": self.head.to_dict(),
            "limits": {
                "pan": self.pan_limits.to_dict(),
                "tilt": self.tilt_limits.to_dict(),
            },
            "moving": False,
        }

    def _motors_state(self) -> JsonObject:
        return {
            "mode": "enabled" if self.motion_enabled else "disabled",
            "bus": "fake",
            "devices": [
                {"name": "head_pan", "kind": "fake_servo"},
                {"name": "head_tilt", "kind": "fake_servo"},
            ],
            "faults": ["emergency_stop"] if self.emergency_stopped else [],
            "temperatures": {},
            "voltage": None,
        }

    def _media_state(self) -> JsonObject:
        return {
            "camera": {"available": True, "enabled": not self.media_released},
            "microphone": {
                "available": True,
                "enabled": not self.media_released,
                "muted": self.microphone_muted,
            },
            "speaker": {
                "available": True,
                "enabled": not self.media_released,
                "muted": self.speaker_muted,
            },
            "owner": "released" if self.media_released else "body_daemon",
            "released": self.media_released,
            "muted": self.microphone_muted,
        }

    def _audio_state(self) -> JsonObject:
        return {
            "directionOfArrival": None,
            "speechDetected": False,
            "inputLevel": 0.0,
            "outputLevel": 0.0,
        }

    def _vision_state(self) -> JsonObject:
        return {
            "frameAvailable": self.frame_available,
            "lastFrameSummary": self.last_frame_summary,
            "privacyMode": self.privacy_mode,
        }

    def _expression_state(self) -> JsonObject:
        gestures: list[JsonValue] = [
            "nod",
            "shake_no",
            "curious_tilt",
            "look_away",
            "look_back",
            "wake",
            "sleep",
            "idle_breathe",
            "small_ack",
        ]
        return {
            "current": self.expression,
            "availableGestures": gestures,
            "idleMode": self.idle_mode,
        }

    def _safety_state(self) -> JsonObject:
        return {
            "motionEnabled": self.motion_enabled,
            "eStop": self.emergency_stopped,
            "watchdog": "ok" if self.watchdog_ok else "expired",
            "maxSpeed": "slow",
            "maxAmplitude": {
                "pan": self.pan_limits.maximum,
                "tilt": self.tilt_limits.maximum,
            },
            "privacy": {
                "camera": "explicit_capture_only",
                "microphone": "muted" if self.microphone_muted else "available",
                "speaker": "available" if not self.speaker_muted else "muted",
                "remoteAccess": "disabled",
            },
        }

    def _tasks_state(self) -> JsonObject:
        return {task_id: task.to_dict() for task_id, task in self.tasks.items()}

    def _calibration_state(self) -> JsonObject:
        return {
            "status": "fake_defaults",
            "centers": {"pan": 0.0, "tilt": 0.0},
            "limits": {
                "pan": self.pan_limits.to_dict(),
                "tilt": self.tilt_limits.to_dict(),
            },
            "requiredSteps": [],
        }

    def _runtime_state(self) -> JsonObject:
        return {
            "uptime": max(0.0, time() - self.started_at),
            "logsSummary": "fake backend ready",
            "config": {"backend": "fake"},
        }

    def mark_task_succeeded(
        self,
        task_id: str,
        name: str,
        target: JsonObject,
        result: JsonObject | None = None,
    ) -> TaskState:
        now = time()
        task = TaskState(
            task_id=task_id,
            name=name,
            status="succeeded",
            progress=1.0,
            target=target,
            started_at=now,
            completed_at=now,
            result={} if result is None else result,
        )
        self.tasks[task_id] = task
        self.last_seen_at = now
        return task


def is_gesture(value: str) -> bool:
    return value in {
        "nod",
        "shake_no",
        "curious_tilt",
        "look_away",
        "look_back",
        "wake",
        "sleep",
        "idle_breathe",
        "small_ack",
    }


def coerce_gesture(value: str) -> BodyGesture:
    if not is_gesture(value):
        msg = f"unsupported gesture: {value}"
        raise ValueError(msg)
    return value  # type: ignore[return-value]
