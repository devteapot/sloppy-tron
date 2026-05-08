"""Launch the Raspberry Pi 5 / ROS 2 Jazzy SloppyTron bridge."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="sloppy_tron_ros_bridge",
                executable="fake_body_pi5_jazzy",
                name="sloppy_tron_pi5_jazzy_fake_body",
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
