"""Gamepad teleop: sensor_msgs/Joy -> control_msgs/JointJog.

Stateless velocity mapping: each tick we read the latest Joy message and
publish the corresponding joint velocities. botx_driver integrates them
into positions (and stops moving if we go quiet for 0.5 s, so releasing
the sticks or unplugging the pad safely freezes the arm).
"""
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from control_msgs.msg import JointJog
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_srvs.srv import Trigger

JOY_STALE = 0.5  # s: stop publishing if the joy driver goes quiet


class JoyTeleop(Node):
    def __init__(self):
        super().__init__("botx_teleop")

        self.declare_parameter("config_file", "")
        cfg_file = self.get_parameter("config_file").value or (
            get_package_share_directory("botx_teleop") + "/config/fantech.yaml"
        )
        with open(cfg_file) as f:
            cfg = yaml.safe_load(f)

        self.deadzone = cfg.get("deadzone", 0.15)
        self.axes = cfg["axes"]          # joint -> {axis, scale}
        self.buttons = cfg.get("buttons", {})
        self.gripper_speed = cfg.get("gripper_speed", 0.02)

        self.joy = None
        self.joy_stamp = 0.0
        self.home_was_pressed = False

        self.create_subscription(Joy, "joy", self.on_joy, 10)
        self.jog_pub = self.create_publisher(JointJog, "joint_jog", 10)
        self.home_client = self.create_client(Trigger, "go_home")

        rate = cfg.get("publish_rate", 25.0)
        self.create_timer(1.0 / rate, self.tick)
        self.get_logger().info(f"Gamepad teleop up (mapping: {cfg_file})")

    def on_joy(self, msg: Joy):
        self.joy = msg
        self.joy_stamp = time.monotonic()

    def button(self, name) -> bool:
        idx = self.buttons.get(name, -1)
        return 0 <= idx < len(self.joy.buttons) and self.joy.buttons[idx] == 1

    def tick(self):
        if self.joy is None or time.monotonic() - self.joy_stamp > JOY_STALE:
            return

        msg = JointJog()
        msg.header.stamp = self.get_clock().now().to_msg()

        for joint, m in self.axes.items():
            idx = m["axis"]
            value = self.joy.axes[idx] if idx < len(self.joy.axes) else 0.0
            if abs(value) < self.deadzone:
                value = 0.0
            msg.joint_names.append(joint)
            msg.velocities.append(value * m["scale"])

        gripper_vel = 0.0
        if self.button("gripper_open"):
            gripper_vel += self.gripper_speed
        if self.button("gripper_close"):
            gripper_vel -= self.gripper_speed
        msg.joint_names.append("gripper_joint")
        msg.velocities.append(gripper_vel)

        self.jog_pub.publish(msg)

        # rising-edge detect on the home button so we call the service once
        home = self.button("go_home")
        if home and not self.home_was_pressed and self.home_client.service_is_ready():
            self.home_client.call_async(Trigger.Request())
            self.get_logger().info("Homing the arm")
        self.home_was_pressed = home


def main():
    rclpy.init()
    node = JoyTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == "__main__":
    main()
