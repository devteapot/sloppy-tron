from glob import glob

from setuptools import find_packages, setup

package_name = "sloppy_tron_description"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/urdf", glob("urdf/*.urdf.xacro")),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/meshes/visual", glob("meshes/visual/*.stl")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="SloppyTron maintainers",
    maintainer_email="sloppy@example.invalid",
    description="Sloppy mascot-inspired ROS description assets for SloppyTron.",
    license="MIT",
)
