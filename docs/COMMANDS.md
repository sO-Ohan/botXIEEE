# botX — The Complete Command Reference

Every command from zero to a moving arm, in order. Copy-paste friendly.
(Deep explanations live in chapters [01](01-robot-arms-and-dof.md)–[10](10-terminal-controller.md);
this page is just the commands.)

---

## 0. One-time machine setup

### 0.1 Distrobox container with ROS 2 Humble

On a non-Ubuntu host (Arch/CachyOS/Fedora…), ROS 2 Humble runs in an
Ubuntu 22.04 distrobox:

```bash
# on the host
sudo pacman -S distrobox podman          # (Arch/CachyOS; use your distro's pkg manager)
distrobox create --name ubuntu --image ubuntu:22.04
distrobox enter ubuntu
```

Inside the container, install ROS 2 Humble + everything this project uses:

```bash
sudo apt update && sudo apt install -y curl gnupg lsb-release software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
     -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
     http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | \
     sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y \
    ros-humble-desktop \
    ros-humble-moveit \
    ros-humble-joy \
    ros-humble-xacro \
    ros-humble-joint-state-publisher-gui \
    python3-colcon-common-extensions \
    python3-serial
```

### 0.2 Firmware toolchain (on the host)

```bash
sudo pacman -S platformio        # or: pip install platformio
```

### 0.3 Serial port permission (on the host, once, then re-login)

```bash
sudo usermod -aG uucp $USER      # Arch/CachyOS; on Ubuntu hosts: dialout
```

---

## 1. Get the code and build

```bash
# host or container - home is shared
git clone https://github.com/sO-Ohan/botXIEEE.git
cd botXIEEE

# build the ROS workspace (inside the container)
distrobox enter ubuntu
cd ~/botXIEEE/ros2_ws                    # adjust path to where you cloned
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

> Add these two `source` lines to the container's `~/.bashrc` to skip
> typing them every session:
> ```bash
> echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
> echo "source ~/botXIEEE/ros2_ws/install/setup.bash" >> ~/.bashrc
> ```

---

## 2. Flash the ESP32 firmware (once, from the host)

```bash
cd ~/botXIEEE/firmware
pio run                    # compile only
pio run -t upload          # compile + flash (ESP32 on /dev/ttyUSB0)
pio device monitor         # serial monitor, 115200 baud - Ctrl+] to exit
```

Sanity check in the monitor (arm servos powered):

```
PING                                 → PONG botx-fw 1.0
T 1500 1500 1500 1500 1500 1500      → all servos gently center
E 0                                  → arm goes limp
```

---

## 3. Run it

> All of these are **inside the container**, in a sourced terminal.
> Everything works with or without the ESP32 plugged in — the driver
> auto-falls-back to simulation and prints which mode it chose.

### 3.1 URDF viewer only (sliders, no MoveIt, no hardware)

```bash
ros2 launch botx_description display.launch.py
```

### 3.2 MoveIt2 + RViz (plan & execute)

```bash
ros2 launch botx_moveit_config demo.launch.py
# variants:
ros2 launch botx_moveit_config demo.launch.py serial_port:=/dev/ttyACM0
ros2 launch botx_moveit_config demo.launch.py use_rviz:=false
```

In RViz: drag the marker on the gripper → **Plan** → **Execute**.
Named poses: Planning tab → Goal State → `home` / `ready`;
switch Planning Group to `gripper` for `open` / `closed`.

### 3.3 Keyboard control (terminal TUI)

```bash
ros2 run botx_tui arm_tui
```

If the header shows `○ DRIVER OFFLINE`, press **`s`** to start the
driver right there — or run 3.2 (or 3.5) in another terminal first.

| Key | Action |
|---|---|
| `↑↓` / `kj` | select joint |
| `←→` / `ad` | move joint (hold = continuous) |
| `1`–`6` | jump to joint |
| `o` / `c` | gripper open / close |
| `+` / `-` | step size |
| `h` | home pose |
| `space` | stop |
| `s` | start driver (when offline) |
| `q` | quit |

### 3.4 Gamepad control (Fantech)

```bash
# terminal 1: MoveIt demo or bare driver (3.2 or 3.5)
# terminal 2:
ros2 launch botx_teleop teleop.launch.py
```

Left stick = base/shoulder, right stick = elbow/wrist-roll,
D-pad = wrist pitch, RB/LB = gripper, Start = home.
Remap in `ros2_ws/src/botx_teleop/config/fantech.yaml` (check indices
with `ros2 topic echo /joy`).

### 3.5 Bare driver only (hardware bring-up / TUI backend)

```bash
ros2 launch botx_driver driver.launch.py
ros2 launch botx_driver driver.launch.py serial_port:=/dev/ttyACM0
```

---

## 4. Handy one-liners

```bash
# who's alive / what's flowing
ros2 node list
ros2 topic list
ros2 topic echo /joint_states --once
ros2 topic hz /joint_states
ros2 action list
rqt_graph

# send the arm home from anywhere
ros2 service call /go_home std_srvs/srv/Trigger

# jog one joint from the CLI (no TUI/gamepad needed)
ros2 topic pub --once /joint_jog control_msgs/msg/JointJog \
  '{joint_names: [base_yaw_joint], displacements: [0.1]}'

# validate the URDF after editing link lengths
xacro ros2_ws/src/botx_description/urdf/botx_arm.urdf.xacro > /tmp/botx.urdf
check_urdf /tmp/botx.urdf

# rebuild after code changes (Python changes need no rebuild thanks to --symlink-install)
cd ~/botXIEEE/ros2_ws && colcon build --symlink-install && source install/setup.bash

# clean rebuild (the fix-everything hammer)
cd ~/botXIEEE/ros2_ws && rm -rf build install log && colcon build --symlink-install
```

---

## 5. Calibration (first time with real hardware)

Edit `ros2_ws/src/botx_driver/config/servo_calibration.yaml`, per joint:

1. Jog the joint positive (TUI `d` key). Real joint moves opposite to
   RViz? → flip the sign of `us_per_unit`.
2. At 0 rad the real joint sits offset from RViz? → adjust `center_us`.
3. Tighten `min_us` / `max_us` before mechanical stops.
4. Restart the launch (no rebuild needed).

---

## 6. Git workflow used for this repo

```bash
git status                       # what changed
git add -A                       # stage everything
git commit -m "message"          # commit
git push                         # publish to github.com/sO-Ohan/botXIEEE
```

---

## 7. If something misbehaves

Quick hits (full detail: [chapter 9](09-troubleshooting.md)):

```bash
ls /dev/ttyUSB* /dev/ttyACM*     # ESP32 visible?
ls /dev/input/js*                # gamepad visible?
ros2 node list                   # stale nodes from another project?
export ROS_DOMAIN_ID=42          # isolate yourself (ALL terminals!)
QT_QPA_PLATFORM=xcb rviz2        # manual rviz on Wayland (launches set it already)
```
