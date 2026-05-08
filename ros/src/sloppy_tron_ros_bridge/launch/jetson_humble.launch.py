"""Launch the Jetson Orin Super / ROS 2 Humble SloppyTron bridge."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="sloppy_tron_ros_bridge",
                executable="fake_body_jetson_humble",
                name="sloppy_tron_jetson_humble_fake_body",
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
