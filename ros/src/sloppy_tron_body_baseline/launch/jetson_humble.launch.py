"""Launch the Jetson / ROS 2 Humble deterministic SloppyTron baseline."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="sloppy_tron_body_baseline",
                executable="baseline_body_jetson_humble",
                name="sloppy_tron_jetson_humble_baseline_body",
                output="screen",
            ),
            Node(
                package="sloppy_tron_ros_bridge",
                executable="slop_bridge_jetson_humble",
                name="sloppy_tron_jetson_humble_slop_bridge",
                output="screen",
            ),
        ]
    )
