"""botX arm driver node.

One node plays three roles:

1. **Controller** - exposes the two FollowJointTrajectory action servers
   that MoveIt2 (moveit_simple_controller_manager) executes against:
       /arm_controller/follow_joint_trajectory
       /gripper_controller/follow_joint_trajectory

2. **Teleop sink** - subscribes to control_msgs/JointJog on /joint_jog
   (published by botx_teleop from the gamepad) and integrates the
   commanded joint velocities.

3. **Hardware bridge** - converts joint positions to servo pulse widths
   using config/servo_calibration.yaml and streams them to the ESP32
   over USB serial. If the port cannot be opened the node keeps running
   as a pure simulator, so RViz/MoveIt work with no hardware attached.

It is the single owner of the robot state: it publishes /joint_states,
from which robot_state_publisher derives TF for RViz and MoveIt.
"""
import math
import threading
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import FollowJointTrajectory
from control_msgs.msg import JointJog
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

MIMIC_JOINT = "gripper_mirror_joint"  # follows gripper_joint (URDF <mimic>)
JOG_TIMEOUT = 0.5    # s without a JointJog message -> stop integrating
HOME_SPEED = 0.6     # rad/s used by the go_home service


class TrajectoryServer(Node):
    def __init__(self):
        super().__init__("botx_driver")

        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("update_rate", 30.0)
        self.declare_parameter("calibration_file", "")

        cal_file = self.get_parameter("calibration_file").value or (
            get_package_share_directory("botx_driver")
            + "/config/servo_calibration.yaml"
        )
        with open(cal_file) as f:
            self.cal = yaml.safe_load(f)["joints"]
        self.joint_names = list(self.cal.keys())

        # single source of truth for where the robot "is"
        self.lock = threading.Lock()
        self.pos = {j: 0.0 for j in self.joint_names}
        self.traj_owned = set()   # joints currently driven by a trajectory
        self.jog = {}             # joint -> commanded velocity (rad/s | m/s)
        self.jog_stamp = 0.0
        self.homing = False

        # hardware link (optional)
        from botx_driver.serial_link import SerialLink
        self.link = SerialLink(self.get_logger())
        if not self.link.open(self.get_parameter("serial_port").value,
                              self.get_parameter("baud").value):
            self.get_logger().warn(
                "No ESP32 found on %s - running in SIMULATION mode "
                "(will keep retrying every 5 s)"
                % self.get_parameter("serial_port").value)

        cb = ReentrantCallbackGroup()
        self.joint_pub = self.create_publisher(JointState, "joint_states", 10)
        self.create_subscription(JointJog, "joint_jog", self.on_jog, 10,
                                 callback_group=cb)
        self.create_service(Trigger, "go_home", self.on_go_home,
                            callback_group=cb)

        self.arm_server = ActionServer(
            self, FollowJointTrajectory,
            "arm_controller/follow_joint_trajectory",
            execute_callback=self.execute_trajectory,
            cancel_callback=lambda req: CancelResponse.ACCEPT,
            callback_group=cb)
        self.gripper_server = ActionServer(
            self, FollowJointTrajectory,
            "gripper_controller/follow_joint_trajectory",
            execute_callback=self.execute_trajectory,
            cancel_callback=lambda req: CancelResponse.ACCEPT,
            callback_group=cb)

        rate = self.get_parameter("update_rate").value
        self.dt = 1.0 / rate
        self.create_timer(self.dt, self.update, callback_group=cb)
        self.create_timer(5.0, self.retry_serial, callback_group=cb)

        self.get_logger().info(
            f"botx_driver up - joints: {', '.join(self.joint_names)}")

    # ------------------------------------------------------------ helpers
    def clamp(self, joint, value):
        c = self.cal[joint]
        return min(max(value, c["min_pos"]), c["max_pos"])

    def pulse_us(self, joint, value):
        c = self.cal[joint]
        us = c["center_us"] + (value - c["center_pos"]) * c["us_per_unit"]
        return int(min(max(us, c["min_us"]), c["max_us"]))

    # ------------------------------------------------------- jog + homing
    def on_jog(self, msg: JointJog):
        with self.lock:
            self.homing = False
            self.jog = {}
            for i, name in enumerate(msg.joint_names):
                if name not in self.cal:
                    continue
                # one-shot position nudge (keyboard TUI sends these:
                # crisp per-keypress steps that stop the instant keys stop)
                if i < len(msg.displacements) and name not in self.traj_owned:
                    self.pos[name] = self.clamp(
                        name, self.pos[name] + msg.displacements[i])
                # continuous velocity jog (gamepad sends these)
                if i < len(msg.velocities):
                    self.jog[name] = msg.velocities[i]
            self.jog_stamp = time.monotonic()

    def on_go_home(self, request, response):
        with self.lock:
            self.homing = True
            self.jog = {}
        response.success = True
        response.message = "Homing"
        return response

    # -------------------------------------------------- trajectory action
    def execute_trajectory(self, goal_handle):
        traj = goal_handle.request.trajectory
        names = list(traj.joint_names)
        result = FollowJointTrajectory.Result()

        unknown = [n for n in names if n not in self.cal]
        if unknown:
            result.error_code = FollowJointTrajectory.Result.INVALID_JOINTS
            result.error_string = f"Unknown joints: {unknown}"
            goal_handle.abort()
            return result

        self.get_logger().info(
            f"Executing trajectory: {len(traj.points)} points, joints {names}")
        with self.lock:
            self.homing = False
            self.traj_owned |= set(names)
            prev_pos = [self.pos[n] for n in names]

        try:
            t0 = time.monotonic()
            prev_t = 0.0
            for point in traj.points:
                t_pt = (point.time_from_start.sec
                        + point.time_from_start.nanosec * 1e-9)
                target = list(point.positions)
                # walk the clock to this waypoint, interpolating linearly
                while True:
                    if goal_handle.is_cancel_requested:
                        goal_handle.canceled()
                        result.error_code = result.SUCCESSFUL
                        return result
                    now = time.monotonic() - t0
                    if now >= t_pt:
                        break
                    if t_pt > prev_t:
                        a = (now - prev_t) / (t_pt - prev_t)
                        with self.lock:
                            for i, n in enumerate(names):
                                self.pos[n] = self.clamp(
                                    n, prev_pos[i] + a * (target[i] - prev_pos[i]))
                    time.sleep(self.dt)
                with self.lock:
                    for i, n in enumerate(names):
                        self.pos[n] = self.clamp(n, target[i])
                prev_t, prev_pos = t_pt, target

            goal_handle.succeed()
            result.error_code = result.SUCCESSFUL
            return result
        finally:
            with self.lock:
                self.traj_owned -= set(names)

    # ------------------------------------------------------- periodic I/O
    def update(self):
        now = time.monotonic()
        with self.lock:
            # integrate gamepad jog velocities (never on trajectory-owned joints)
            if self.jog and now - self.jog_stamp < JOG_TIMEOUT:
                for name, vel in self.jog.items():
                    if name not in self.traj_owned:
                        self.pos[name] = self.clamp(
                            name, self.pos[name] + vel * self.dt)
            # slow slew back to the home pose after the go_home service
            if self.homing:
                done = True
                for name in self.joint_names:
                    if name in self.traj_owned:
                        continue
                    step = HOME_SPEED * self.dt
                    if abs(self.pos[name]) > step:
                        self.pos[name] -= math.copysign(step, self.pos[name])
                        done = False
                    else:
                        self.pos[name] = 0.0
                self.homing = not done
            snapshot = dict(self.pos)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names + [MIMIC_JOINT]
        msg.position = [snapshot[j] for j in self.joint_names]
        msg.position.append(snapshot["gripper_joint"])  # mimic follows 1:1
        self.joint_pub.publish(msg)

        if self.link.is_open:
            pulses = [0] * 6
            for name in self.joint_names:
                pulses[self.cal[name]["channel"]] = self.pulse_us(
                    name, snapshot[name])
            self.link.write_line("T " + " ".join(str(p) for p in pulses))

    def retry_serial(self):
        if not self.link.is_open:
            self.link.open(self.get_parameter("serial_port").value,
                           self.get_parameter("baud").value)


def main():
    rclpy.init()
    node = TrajectoryServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.link.close()
        node.destroy_node()


if __name__ == "__main__":
    main()
