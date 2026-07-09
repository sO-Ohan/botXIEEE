"""Standalone driver (no MoveIt): useful for first hardware bring-up.

    ros2 launch botx_driver driver.launch.py serial_port:=/dev/ttyUSB0

Then move single joints from another terminal, e.g.:

    ros2 topic pub -r 10 /joint_jog control_msgs/msg/JointJog \
      '{joint_names: [base_yaw_joint], velocities: [0.3]}'
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
        Node(
            package="botx_driver",
            executable="trajectory_server",
            output="screen",
            parameters=[{"serial_port": LaunchConfiguration("serial_port")}],
        ),
    ])
