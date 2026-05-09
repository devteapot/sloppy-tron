from setuptools import find_packages, setup

package_name = "sloppy_tron_ros_bridge"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (
            f"share/{package_name}/launch",
            [
                "launch/jetson_humble.launch.py",
                "launch/pi5_jazzy.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools", "slop-ai>=0.2.0"],
    zip_safe=True,
    maintainer="SloppyTron maintainers",
    maintainer_email="sloppy@example.invalid",
    description="ROS 2 bridge nodes for the SloppyTron SLOP body provider.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "slop_bridge = sloppy_tron_ros_bridge.slop_bridge_node:main",
            "slop_bridge_pi5_jazzy = "
            "sloppy_tron_ros_bridge.slop_bridge_node:pi5_jazzy_main",
            "slop_bridge_jetson_humble = "
            "sloppy_tron_ros_bridge.slop_bridge_node:jetson_humble_main",
            "fake_body = sloppy_tron_ros_bridge.fake_body_node:main",
            "fake_body_pi5_jazzy = "
            "sloppy_tron_ros_bridge.fake_body_node:pi5_jazzy_main",
            "fake_body_jetson_humble = "
            "sloppy_tron_ros_bridge.fake_body_node:jetson_humble_main",
        ],
    },
)
