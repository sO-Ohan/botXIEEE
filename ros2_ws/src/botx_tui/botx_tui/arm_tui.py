"""botX terminal controller - a curses TUI for jogging the arm per joint.

    ros2 run botx_tui arm_tui        (botx_driver must be running)

Every keypress publishes a one-shot position nudge (JointJog.displacements)
to /joint_jog; the driver clamps it to the joint limits and streams it to
the ESP32. Hold a key and the OS key-repeat gives continuous motion that
stops the instant you let go. The right-hand gauges always show the REAL
state echoed back on /joint_states - the TUI displays truth, not wishes.

Keys
    up/down, k/j ... select joint          1-6 ...... jump to joint
    left/right, a/d  move selected joint   o / c .... gripper open/close
    +/- ............ step size             h ........ home pose
    space .......... stop (zero jog)       q ........ quit
    s .............. start botx_driver from here (if it isn't running)
"""
import curses
import locale
import math
import subprocess
import threading
import time

import rclpy
from control_msgs.msg import JointJog
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

#            joint name             label       min      max     unit
JOINTS = [
    ("base_yaw_joint",        "Base yaw",     -1.5708, 1.5708, "rad"),
    ("shoulder_pitch_joint",  "Shoulder",     -1.5708, 1.5708, "rad"),
    ("elbow_pitch_joint",     "Elbow",        -1.5708, 1.5708, "rad"),
    ("wrist_pitch_joint",     "Wrist pitch",  -1.5708, 1.5708, "rad"),
    ("wrist_roll_joint",      "Wrist roll",   -1.5708, 1.5708, "rad"),
    ("gripper_joint",         "Gripper",       0.0,    0.0225, "m"),
]
STEPS_RAD = [0.005, 0.02, 0.05]        # selectable step sizes (rad/keypress)
GRIP_STEP_FACTOR = 0.04                # gripper meters per rad of step
BAR_W = 26
LOGO = " botX  ARM  CONTROL "
DRIVER_LOG = "/tmp/botx_driver_tui.log"


class TuiNode(Node):
    def __init__(self):
        super().__init__("botx_tui")
        self.state = {}
        self.state_stamp = 0.0
        self.create_subscription(JointState, "joint_states", self._on_js, 10)
        self.jog_pub = self.create_publisher(JointJog, "joint_jog", 10)
        self.home_client = self.create_client(Trigger, "go_home")

    def _on_js(self, msg):
        self.state.update(zip(msg.name, msg.position))
        self.state_stamp = time.monotonic()

    @property
    def driver_online(self):
        return time.monotonic() - self.state_stamp < 1.0

    def nudge(self, joint, delta):
        msg = JointJog()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = [joint]
        msg.displacements = [delta]
        msg.velocities = [0.0]
        self.jog_pub.publish(msg)

    def stop(self):
        msg = JointJog()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = [j[0] for j in JOINTS]
        msg.velocities = [0.0] * len(JOINTS)
        self.jog_pub.publish(msg)

    def home(self):
        if self.home_client.service_is_ready():
            self.home_client.call_async(Trigger.Request())
            return True
        return False


def fmt_pos(value, unit):
    if unit == "rad":
        return f"{math.degrees(value):+7.1f}°"
    return f"{value * 1000:6.1f}mm"


def draw(scr, node, sel, step_i, flash):
    scr.erase()
    h, w = scr.getmaxyx()
    dim = curses.A_DIM
    bold = curses.A_BOLD

    def put(y, x, text, attr=0):
        if 0 <= y < h:
            try:
                scr.addstr(y, x, text[: max(0, w - x - 1)], attr)
            except curses.error:
                pass

    # ---- header ----
    put(0, 0, "═" * (w - 1), curses.color_pair(4))
    put(0, max(0, (w - len(LOGO)) // 2), LOGO,
        curses.color_pair(4) | bold | curses.A_REVERSE)
    online = node.driver_online
    status = "● DRIVER ONLINE " if online else "○ DRIVER OFFLINE"
    put(1, 2, status, curses.color_pair(1 if online else 3) | bold)
    step_deg = math.degrees(STEPS_RAD[step_i])
    put(1, 22, f"step: {step_deg:.1f}°/press   [+/-] change", dim)
    if flash:
        put(1, w - len(flash) - 2, flash, curses.color_pair(2) | bold)
    if not online:
        put(2, 2, "no /joint_states - press [s] to start the driver here, "
                  "or launch demo.launch.py / driver.launch.py",
            curses.color_pair(3))

    # ---- joint gauges ----
    for i, (name, label, lo, hi, unit) in enumerate(JOINTS):
        y = 3 + i * 2
        selected = i == sel
        pos = node.state.get(name, 0.0)
        frac = 0.0 if hi == lo else (pos - lo) / (hi - lo)
        frac = min(max(frac, 0.0), 1.0)
        fill = int(round(frac * BAR_W))

        arrow = "▶" if selected else " "
        attr = (curses.color_pair(2) | bold) if selected else 0
        put(y, 1, f"{arrow} {i + 1} {label:<12}", attr)

        bar_x = 19
        bar = "█" * fill + "─" * (BAR_W - fill)
        put(y, bar_x, "[", dim)
        put(y, bar_x + 1, bar,
            curses.color_pair(2 if selected else 1))
        put(y, bar_x + 1 + BAR_W, "]", dim)
        # center tick (0 rad / mid travel)
        put(y, bar_x + 1 + BAR_W // 2, "┼", dim)
        put(y, bar_x + BAR_W + 4, fmt_pos(pos, unit), attr or dim)
        limits = (f"{math.degrees(lo):+.0f}..{math.degrees(hi):+.0f}°"
                  if unit == "rad" else "0..22.5mm")
        put(y + 1, bar_x + 1, limits, dim)

    # ---- footer ----
    fy = 3 + len(JOINTS) * 2 + 1
    put(fy, 0, "─" * (w - 1), dim)
    put(fy + 1, 2,
        "↑↓/kj select   ←→/ad move   1-6 jump   o/c gripper", dim | bold)
    put(fy + 2, 2,
        "+/- step   h home   space stop   q quit", dim | bold)
    scr.refresh()


def run(scr, node):
    locale.setlocale(locale.LC_ALL, "")
    curses.curs_set(0)
    curses.use_default_colors()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_BLUE, -1)
    scr.timeout(50)   # draw at ~20 fps while idle
    scr.keypad(True)

    sel, step_i = 0, 1
    flash, flash_until = "", 0.0
    driver_proc = None

    while True:
        name, _, _, _, unit = JOINTS[sel]
        step = STEPS_RAD[step_i]
        if unit == "m":
            step *= GRIP_STEP_FACTOR

        key = scr.getch()
        if key in (ord("q"), 27):                      # q / Esc
            node.stop()
            if driver_proc is not None and driver_proc.poll() is None:
                driver_proc.terminate()
            return
        elif key == ord("s") and not node.driver_online:
            # convenience: spawn the driver right here, logs to a file so
            # they don't trample the curses screen
            if driver_proc is None or driver_proc.poll() is not None:
                log = open(DRIVER_LOG, "w")
                driver_proc = subprocess.Popen(
                    ["ros2", "run", "botx_driver", "trajectory_server"],
                    stdout=log, stderr=subprocess.STDOUT)
                flash = f"driver started (log: {DRIVER_LOG})"
                flash_until = time.monotonic() + 3.0
        elif key in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(JOINTS)
        elif key in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(JOINTS)
        elif ord("1") <= key <= ord("6"):
            sel = key - ord("1")
        elif key in (curses.KEY_RIGHT, ord("d")):
            node.nudge(name, +step)
        elif key in (curses.KEY_LEFT, ord("a")):
            node.nudge(name, -step)
        elif key in (ord("+"), ord("=")):
            step_i = min(step_i + 1, len(STEPS_RAD) - 1)
        elif key == ord("-"):
            step_i = max(step_i - 1, 0)
        elif key == ord("o"):
            node.nudge("gripper_joint", +STEPS_RAD[step_i] * GRIP_STEP_FACTOR)
        elif key == ord("c"):
            node.nudge("gripper_joint", -STEPS_RAD[step_i] * GRIP_STEP_FACTOR)
        elif key == ord("h"):
            ok = node.home()
            flash = "HOMING..." if ok else "driver offline"
            flash_until = time.monotonic() + 1.5
        elif key == ord(" "):
            node.stop()
            flash = "STOP"
            flash_until = time.monotonic() + 1.0

        if time.monotonic() > flash_until:
            flash = ""
        draw(scr, node, sel, step_i, flash)


def main():
    rclpy.init()
    node = TuiNode()

    def _spin():
        try:
            rclpy.spin(node)
        except Exception:
            pass  # shutdown race on exit; the TUI is already closing

    spinner = threading.Thread(target=_spin, daemon=True)
    spinner.start()
    try:
        curses.wrapper(run, node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
