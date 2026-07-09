"""Full MoveIt2 demo for the botX arm.

    ros2 launch botx_moveit_config demo.launch.py
    ros2 launch botx_moveit_config demo.launch.py serial_port:=/dev/ttyUSB0
    ros2 launch botx_moveit_config demo.launch.py use_rviz:=false

Starts:
  * robot_state_publisher   (URDF -> TF)
  * move_group              (MoveIt2 planning + execution)
  * botx_driver             (trajectory action servers; drives the real
                             ESP32 if the serial port opens, otherwise
                             simulates the servos)
  * RViz2 with the MotionPlanning plugin
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("botx_arm", package_name="botx_moveit_config")
        .robot_description(file_path="config/botx.urdf.xacro")
        .robot_description_semantic(file_path="config/botx.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
        )
        .to_moveit_configs()
    )

    rviz_config = str(moveit_config.package_path / "rviz" / "moveit.rviz")

    return LaunchDescription([
        DeclareLaunchArgument("use_rviz", default_value="true"),
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/ttyUSB0",
            description="ESP32 USB serial port. If it cannot be opened, "
                        "the driver runs in simulation mode.",
        ),

        # SRDF declares the arm fixed to 'world'; provide that frame.
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["--frame-id", "world", "--child-frame-id", "base_link"],
        ),

        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[moveit_config.robot_description],
        ),

        Node(
            package="botx_driver",
            executable="trajectory_server",
            output="screen",
            parameters=[{"serial_port": LaunchConfiguration("serial_port")}],
        ),

        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[moveit_config.to_dict()],
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            condition=IfCondition(LaunchConfiguration("use_rviz")),
            # On Wayland sessions RViz's Qt window opens but the Ogre/GLX 3D
            # viewport fails ("Invalid parentWindowHandle"); forcing the X11
            # Qt platform (XWayland) fixes it and is harmless on plain X11.
            additional_env={"QT_QPA_PLATFORM": "xcb"},
            arguments=["-d", rviz_config],
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
                moveit_config.joint_limits,
            ],
        ),
    ])
