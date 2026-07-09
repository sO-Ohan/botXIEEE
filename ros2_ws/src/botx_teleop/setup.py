from setuptools import setup

package_name = "botx_teleop"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", ["config/fantech.yaml"]),
        ("share/" + package_name + "/launch", ["launch/teleop.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Monjurul Hasan Sohan",
    maintainer_email="shawonparvez@outlook.com",
    description="Gamepad teleop for the botX 6-DOF arm",
    license="MIT",
    entry_points={
        "console_scripts": [
            "joy_teleop = botx_teleop.joy_teleop:main",
        ],
    },
)
