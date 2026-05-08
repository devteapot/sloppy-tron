"""Fake body backend used before hardware is present."""

from __future__ import annotations

from itertools import count

from sloppy_tron.provider.contract import (
    BodyGesture,
    IdleMode,
    JsonObject,
    affordances_as_dicts,
)
from sloppy_tron.provider.state import ProviderState, TaskState


class FakeBodyBackend:
    """In-memory backend that mirrors the first real body contract."""

    def __init__(self) -> None:
        self._state = ProviderState()
        self._task_numbers = count(1)

    def snapshot(self) -> JsonObject:
        return self._state.to_dict()

    def affordances(self) -> list[JsonObject]:
        return affordances_as_dicts()

    def wake(self) -> TaskState:
        self._state.motion_enabled = True
        self._state.microphone_muted = False
        self._state.expression = "awake"
        self._state.idle_mode = "attentive"
        return self._complete("wake", {"posture": "awake"})

    def sleep(self) -> TaskState:
        self._state.motion_enabled = False
        self._state.microphone_muted = True
        self._state.expression = "sleep"
        self._state.idle_mode = "off"
        self._state.head.pan = 0.0
        self._state.head.tilt = 0.0
        return self._complete("sleep", {"posture": "sleep"})

    def look_at_angles(self, pan: float, tilt: float) -> TaskState:
        clamped_pan = self._state.pan_limits.clamp(pan)
        clamped_tilt = self._state.tilt_limits.clamp(tilt)
        if self._state.motion_enabled and not self._state.emergency_stopped:
            self._state.head.pan = clamped_pan
            self._state.head.tilt = clamped_tilt
        return self._complete(
            "look_at_angles",
            {"pan": pan, "tilt": tilt},
            {
                "accepted": self._state.motion_enabled
                and not self._state.emergency_stopped,
                "pan": clamped_pan,
                "tilt": clamped_tilt,
            },
        )

    def look_at_point(self, x: float, y: float, z: float) -> TaskState:
        pan = self._state.pan_limits.clamp(x * self._state.pan_limits.maximum)
        tilt = self._state.tilt_limits.clamp(y * self._state.tilt_limits.maximum)
        task = self.look_at_angles(pan=pan, tilt=tilt)
        task.name = "look_at_point"
        task.target = {"x": x, "y": y, "z": z}
        return task

    def look_toward_sound(self) -> TaskState:
        task = self.look_at_angles(pan=0.0, tilt=0.0)
        task.name = "look_toward_sound"
        task.target = {"directionOfArrival": None}
        return task

    def gesture(self, gesture: BodyGesture) -> TaskState:
        if gesture == "wake":
            return self.wake()
        if gesture == "sleep":
            return self.sleep()
        self._state.expression = gesture
        return self._complete("gesture", {"gesture": gesture})

    def capture_frame(self) -> TaskState:
        captured = not self._state.media_released
        self._state.frame_available = captured
        self._state.last_frame_summary = (
            "fake frame captured" if captured else "media released"
        )
        return self._complete(
            "capture_frame",
            {"privacyMode": self._state.privacy_mode},
            {"captured": captured},
        )

    def set_idle_mode(self, idle_mode: IdleMode) -> TaskState:
        self._state.idle_mode = idle_mode
        return self._complete("set_idle_mode", {"idleMode": idle_mode})

    def release_media(self) -> TaskState:
        self._state.media_released = True
        return self._complete("release_media", {}, {"released": True})

    def acquire_media(self) -> TaskState:
        self._state.media_released = False
        return self._complete("acquire_media", {}, {"released": False})

    def enable_motion(self) -> TaskState:
        accepted = not self._state.emergency_stopped
        self._state.motion_enabled = accepted
        return self._complete("enable_motion", {}, {"accepted": accepted})

    def disable_motion(self) -> TaskState:
        self._state.motion_enabled = False
        return self._complete("disable_motion", {}, {"accepted": True})

    def emergency_stop(self) -> TaskState:
        self._state.motion_enabled = False
        self._state.emergency_stopped = True
        self._state.expression = "emergency_stop"
        return self._complete("emergency_stop", {}, {"accepted": True})

    def _complete(
        self,
        name: str,
        target: JsonObject,
        result: JsonObject | None = None,
    ) -> TaskState:
        task_id = f"fake-task-{next(self._task_numbers)}"
        return self._state.mark_task_succeeded(task_id, name, target, result)
