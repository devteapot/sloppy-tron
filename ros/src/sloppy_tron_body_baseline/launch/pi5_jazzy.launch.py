"""Launch the Raspberry Pi 5 / ROS 2 Jazzy deterministic SloppyTron baseline."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="sloppy_tron_body_baseline",
                executable="baseline_body_pi5_jazzy",
                name="sloppy_tron_pi5_jazzy_baseline_body",
                output="screen",
            ),
            Node(
                package="sloppy_tron_ros_bridge",
                executable="slop_bridge_pi5_jazzy",
                name="sloppy_tron_pi5_jazzy_slop_bridge",
                output="screen",
            ),
        ]
    )
