from setuptools import setup

package_name = "botx_tui"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Monjurul Hasan Sohan",
    maintainer_email="shawonparvez@outlook.com",
    description="Terminal keyboard controller (curses TUI) for the botX arm",
    license="MIT",
    entry_points={
        "console_scripts": [
            "arm_tui = botx_tui.arm_tui:main",
        ],
    },
)
