"""Visualize the botX arm URDF in RViz with slider control.

    ros2 launch botx_description display.launch.py

Uses joint_state_publisher_gui so each joint can be moved with a slider —
no MoveIt, no hardware. This is the 'hello world' of a robot description.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory("botx_description")
    xacro_file = os.path.join(pkg, "urdf", "botx_arm.urdf.xacro")
    rviz_config = os.path.join(pkg, "rviz", "display.rviz")

    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str,
    )

    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="joint_state_publisher_gui",
            executable="joint_state_publisher_gui",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            # On Wayland sessions RViz's Qt window opens but the Ogre/GLX 3D
            # viewport fails ("Invalid parentWindowHandle"); forcing the X11
            # Qt platform (XWayland) fixes it and is harmless on plain X11.
            additional_env={"QT_QPA_PLATFORM": "xcb"},
            arguments=["-d", rviz_config],
        ),
    ])
