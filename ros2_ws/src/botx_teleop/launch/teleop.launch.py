"""Gamepad teleop for the botX arm.

Run this IN ADDITION to either demo.launch.py (MoveIt) or
driver.launch.py (bare driver):

    ros2 launch botx_teleop teleop.launch.py

Starts the joy driver (reads /dev/input/js*) and the mapping node.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "config_file", default_value="",
            description="Custom gamepad mapping yaml (default: Fantech)"),
        Node(
            package="joy",
            executable="joy_node",
            parameters=[{"deadzone": 0.05, "autorepeat_rate": 25.0}],
        ),
        Node(
            package="botx_teleop",
            executable="joy_teleop",
            output="screen",
            parameters=[{"config_file": LaunchConfiguration("config_file")}],
        ),
    ])
