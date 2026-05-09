"""Semantic body provider contract shared by fake and real backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PROVIDER_ID = "body"

AffordanceRisk = Literal["read_only", "safe", "guarded", "dangerous"]
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
TaskStatus = Literal["accepted", "running", "succeeded", "failed", "cancelled"]
BodyGesture = Literal[
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
IdleMode = Literal["off", "breathing", "attentive"]


@dataclass(frozen=True, slots=True)
class Affordance:
    """A semantic operation exposed by the body provider."""

    name: str
    risk: AffordanceRisk
    description: str

    def to_dict(self) -> JsonObject:
        return {
            "name": self.name,
            "risk": self.risk,
            "description": self.description,
        }


AFFORDANCES: tuple[Affordance, ...] = (
    Affordance("refresh", "read_only", "Refresh cached body state."),
    Affordance(
        "capture_state_snapshot",
        "read_only",
        "Return a point-in-time body state snapshot.",
    ),
    Affordance(
        "get_camera_frame",
        "read_only",
        "Return the most recent explicitly captured camera frame.",
    ),
    Affordance("list_gestures", "read_only", "List available body gestures."),
    Affordance("scan_motors", "read_only", "Inspect motor bus state."),
    Affordance("play_test_sound", "read_only", "Play a short local test sound."),
    Affordance("wake", "safe", "Move into an awake, attentive posture."),
    Affordance("sleep", "safe", "Move into a conservative sleep posture."),
    Affordance("look_at_angles", "safe", "Look at clamped pan and tilt angles."),
    Affordance("look_at_point", "safe", "Look toward a point in body coordinates."),
    Affordance("look_toward_sound", "safe", "Look toward audio direction of arrival."),
    Affordance("gesture", "safe", "Run a named semantic body gesture."),
    Affordance("capture_frame", "safe", "Explicitly capture one camera frame."),
    Affordance("set_idle_mode", "safe", "Set idle expression behavior."),
    Affordance("set_expression", "safe", "Set the current non-motion expression."),
    Affordance("set_volume", "safe", "Set speaker output volume."),
    Affordance("set_microphone_gain", "safe", "Set microphone input gain."),
    Affordance("release_media", "safe", "Release media devices to another process."),
    Affordance("acquire_media", "safe", "Acquire media devices for the body daemon."),
    Affordance("enable_motion", "guarded", "Enable motion after safety checks."),
    Affordance("disable_motion", "guarded", "Disable body motion."),
    Affordance("emergency_stop", "safe", "Immediately disable motion."),
    Affordance("set_motor_mode", "dangerous", "Change low-level motor mode."),
    Affordance("calibrate_center", "dangerous", "Persist motor center calibration."),
    Affordance("calibrate_limits", "dangerous", "Persist motor travel limits."),
    Affordance("raw_motor_command", "dangerous", "Send a raw motor command."),
    Affordance("update_body_firmware", "dangerous", "Update controller firmware."),
    Affordance(
        "emergency_stop_reset",
        "dangerous",
        "Reset emergency stop after physical inspection.",
    ),
)

IMPLEMENTED_AFFORDANCE_NAMES: frozenset[str] = frozenset(
    {
        "refresh",
        "capture_state_snapshot",
        "wake",
        "sleep",
        "look_at_angles",
        "look_at_point",
        "look_toward_sound",
        "gesture",
        "capture_frame",
        "set_idle_mode",
        "release_media",
        "acquire_media",
        "enable_motion",
        "disable_motion",
        "emergency_stop",
    }
)
FUTURE_AFFORDANCE_NAMES: frozenset[str] = (
    frozenset(affordance.name for affordance in AFFORDANCES)
    - IMPLEMENTED_AFFORDANCE_NAMES
)


def affordances_as_dicts() -> list[JsonObject]:
    return [affordance.to_dict() for affordance in AFFORDANCES]
