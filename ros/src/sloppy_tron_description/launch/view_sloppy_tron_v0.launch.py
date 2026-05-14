from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    urdf_path = PathJoinSubstitution(
        [
            FindPackageShare("sloppy_tron_description"),
            "urdf",
            "sloppy_tron_v0.urdf.xacro",
        ]
    )
    robot_description = {"robot_description": Command(["xacro ", urdf_path])}

    return LaunchDescription(
        [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="sloppy_tron_v0_state_publisher",
                output="screen",
                parameters=[robot_description],
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="sloppy_tron_v0_joint_state_gui",
                output="screen",
            ),
        ]
    )
