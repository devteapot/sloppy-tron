"""Platform profiles for ROS bridge entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PlatformId = Literal["pi5_jazzy", "jetson_humble"]


@dataclass(frozen=True, slots=True)
class BridgePlatform:
    """Runtime defaults for a specific board and ROS distro pairing."""

    id: PlatformId
    label: str
    board: str
    ros_distro: str
    ubuntu_version: str
    python_version: str
    socket_path: str
    state_topic: str = "body_state"
    command_topic: str = "body_command"
    publish_hz: float = 10.0
    register_provider: bool = True


PI5_JAZZY = BridgePlatform(
    id="pi5_jazzy",
    label="Raspberry Pi 5 / ROS 2 Jazzy",
    board="raspberry_pi_5",
    ros_distro="jazzy",
    ubuntu_version="24.04",
    python_version="3.12",
    socket_path="/tmp/slop/sloppy-tron-pi5-jazzy.sock",
)

JETSON_HUMBLE = BridgePlatform(
    id="jetson_humble",
    label="Jetson Orin Super / ROS 2 Humble",
    board="jetson_orin_super",
    ros_distro="humble",
    ubuntu_version="22.04",
    python_version="3.10",
    socket_path="/tmp/slop/sloppy-tron-jetson-humble.sock",
)

PLATFORMS: dict[PlatformId, BridgePlatform] = {
    PI5_JAZZY.id: PI5_JAZZY,
    JETSON_HUMBLE.id: JETSON_HUMBLE,
}


def get_platform(platform_id: str) -> BridgePlatform:
    try:
        return PLATFORMS[platform_id]  # type: ignore[index]
    except KeyError as exc:
        names = ", ".join(sorted(PLATFORMS))
        message = f"unsupported bridge platform {platform_id!r}; use {names}"
        raise ValueError(message) from exc


def platform_ids() -> tuple[PlatformId, ...]:
    return tuple(PLATFORMS)
