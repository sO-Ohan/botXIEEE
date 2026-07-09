# botX — 6-DOF Robotic Arm on ROS 2

A complete, teachable control stack for a generic 6-DOF aluminum robotic arm
(ROT3U-style kit): **ESP32 + PCA9685** firmware, a **ROS 2 Humble** workspace
with a hand-written **URDF**, **MoveIt 2** motion planning, **RViz**
visualization, and **gamepad teleoperation** — plus classroom documentation
explaining every layer.

```
                       ┌─────────────────────────────────────────────┐
                       │                ROS 2 (PC)                   │
 ┌──────────┐  /joy    │ ┌────────────┐ FollowJointTrajectory        │
 │ Fantech  ├──────────┼─► botx_teleop├──────────┐                   │
 │ gamepad  │          │ └────────────┘ JointJog ▼                   │
 └──────────┘          │ ┌─────────┐          ┌──────────────┐       │  USB serial   ┌───────┐  I2C  ┌─────────┐ PWM ┌──────────┐
                       │ │ MoveIt2 ├──────────►  botx_driver ├───────┼───────────────► ESP32 ├───────► PCA9685 ├─────► 6 servos │
                       │ │ + RViz  │          └──────┬───────┘       │ "T 1500 ..."  └───────┘       └─────────┘     └──────────┘
                       │ └────▲────┘                 │ /joint_states │
                       │      └──────────────────────┘               │
                       └─────────────────────────────────────────────┘
```

## Repository layout

| Path | What it is |
|---|---|
| `firmware/` | ESP32 firmware (PlatformIO, Arduino framework) — dumb/safe servo bridge |
| `ros2_ws/src/botx_description/` | URDF/xacro robot model + RViz display launch |
| `ros2_ws/src/botx_moveit_config/` | MoveIt 2 configuration (SRDF, IK, controllers) + demo launch |
| `ros2_ws/src/botx_driver/` | Trajectory action servers + serial bridge (auto-simulates without hardware) |
| `ros2_ws/src/botx_teleop/` | Fantech gamepad teleop (`joy` → `JointJog`) |
| `ros2_ws/src/botx_tui/` | Terminal keyboard controller (curses TUI with live joint gauges) |
| `docs/` | The class: arms & DOF → hardware → firmware → URDF → ROS 2 → MoveIt 2 → teleop |

## Quickstart

Everything ROS runs inside the `ubuntu` distrobox (ROS 2 Humble):

```bash
distrobox enter ubuntu

# build once
cd ~/Documents/botXIEEE/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# 1. just look at the robot model (sliders, no MoveIt)
ros2 launch botx_description display.launch.py

# 2. full MoveIt2 demo (works with or without the real arm attached)
ros2 launch botx_moveit_config demo.launch.py

# 3. gamepad teleop (second terminal, alongside 2)
ros2 launch botx_teleop teleop.launch.py

# 4. terminal keyboard controller (second terminal, alongside 2)
ros2 run botx_tui arm_tui
```

Flash the firmware once (from the host, ESP32 on USB):

```bash
cd firmware && pio run -t upload
```

**In a hurry?** → [docs/COMMANDS.md](docs/COMMANDS.md) has every command
from zero (distrobox + ROS install + clone) to a moving arm, in order.

## The class

1. [What is a robotic arm? What is a DOF?](docs/01-robot-arms-and-dof.md)
2. [Hardware & electronics](docs/02-hardware-and-electronics.md)
3. [The ESP32 firmware](docs/03-firmware-esp32.md)
4. [URDF — describing a robot](docs/04-urdf-explained.md)
5. [The ROS 2 workspace](docs/05-ros2-workspace.md)
6. [MoveIt 2 & RViz](docs/06-moveit2-and-rviz.md)
7. [Gamepad teleoperation](docs/07-gamepad-teleop.md)
8. [Class demo script (lesson plan)](docs/08-class-demo-script.md)
9. [Troubleshooting](docs/09-troubleshooting.md)
10. [Terminal keyboard controller (TUI)](docs/10-terminal-controller.md)

## License

MIT
