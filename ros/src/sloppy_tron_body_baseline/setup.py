from setuptools import find_packages, setup

package_name = "sloppy_tron_body_baseline"

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
        (
            f"share/{package_name}/urdf",
            ["urdf/sloppy_tron_baseline.urdf.xacro"],
        ),
        (
            f"share/{package_name}/config",
            ["config/joints.yaml", "config/limits.yaml"],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="SloppyTron maintainers",
    maintainer_email="sloppy@example.invalid",
    description="Deterministic Reachy-compatible ROS body baseline for SloppyTron.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "baseline_body = sloppy_tron_body_baseline.baseline_body_node:main",
            "baseline_body_pi5_jazzy = "
            "sloppy_tron_body_baseline.baseline_body_node:pi5_jazzy_main",
            "baseline_body_jetson_humble = "
            "sloppy_tron_body_baseline.baseline_body_node:jetson_humble_main",
        ],
    },
)
