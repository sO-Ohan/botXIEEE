# 9. Troubleshooting

## Ghost joints / "Joint 'shoulder_pan' not found in model"

Another ROS process is publishing `/joint_states` with a different robot's
joint names — typically a **leftover launch from another arm workspace**
(this happened on this very machine with an old `learm_ws` demo left
running in two terminals). ROS 2 nodes discover each other automatically
on the same machine/network.

```bash
ros2 node list          # anything you don't recognize?
ps aux | grep ros2      # find and close the old terminals
```

Quick isolation instead: `export ROS_DOMAIN_ID=42` in **every** terminal
of your session.

## Serial port

- `ls /dev/ttyUSB*` — nothing? Bad cable (charge-only USB cables are a
  plague), or the CP210x/CH340 driver didn't bind (`dmesg | tail`).
- Permission denied → add yourself to the owning group and re-login:
  `sudo usermod -aG dialout $USER` (group may be `uucp` on Arch/CachyOS).
- Driver says SIMULATION but the ESP32 is plugged in → something else
  holds the port (a forgotten `pio device monitor`!). Only one program
  can own the port at a time.
- Port is sometimes `/dev/ttyACM0`:
  `ros2 launch botx_moveit_config demo.launch.py serial_port:=/dev/ttyACM0`

## Arm behaves violently or reboots

| Symptom | Likely cause |
|---|---|
| ESP32 reboots when servos move | servos powered from USB/ESP32 — use the dedicated PSU into V+ |
| all servos jitter | PSU too weak, or grounds not common |
| one joint slams to an extreme | wrong `us_per_unit` sign or `center_us` in `servo_calibration.yaml` |
| joint buzzes at rest | fighting a mechanical stop — tighten `min_us`/`max_us` |
| arm mirrors RViz | flip that joint's `us_per_unit` sign |

## MoveIt

- **Planning fails instantly** → target outside the workspace (~35 cm
  dome) or start state in collision. Drag the marker closer.
- **"Unable to solve IK"** with orientation-constrained targets → expected
  on a 5-DOF arm; we use position-only IK (ch. 6).
- **Execute does nothing** → is `botx_driver` running? `ros2 action list`
  must show `/arm_controller/follow_joint_trajectory`.
- **RViz shows the arm at weird angles at startup** → no `/joint_states`
  publisher; again, the driver isn't running.

## Gamepad

- `ls /dev/input/js*` — nothing? Try the pad's mode/Analog button; some
  Fantech pads need it. Check `dmesg | tail`.
- Pad detected but wrong axes → `ros2 topic echo /joy`, remap in
  `botx_teleop/config/fantech.yaml` (ch. 7).
- Nothing moves → is `joy_node` publishing? `ros2 topic hz /joy`.

## RViz opens but shows no 3D view / no robot (Wayland)

On a Wayland desktop (KDE/GNOME on CachyOS/Arch), RViz's Qt window opens
— panels, MotionPlanning controls — but the central 3D viewport fails to
create. The terminal shows repeated:

```
RenderingAPIException: Invalid parentWindowHandle (wrong server or screen)
in GLXWindow::create
```

Cause: Qt picks the native Wayland backend while RViz's Ogre renderer
needs an X11 (GLX) window. Fix: run RViz under XWayland:

```bash
QT_QPA_PLATFORM=xcb rviz2
```

Both launch files in this repo already set this for their RViz nodes, so
`display.launch.py` and `demo.launch.py` are immune. If you ever launch
`rviz2` by hand, prefix it as above (or export it in your shell).

## Distrobox

- GUI apps (RViz) need the host X/Wayland socket — distrobox forwards it
  by default; if RViz won't open, run `xhost +si:localuser:$USER` on the host.
- Devices appear inside the container automatically (`/dev` is shared),
  but group permissions come from the host.

## Nuclear option

```bash
cd ros2_ws && rm -rf build install log && colcon build --symlink-install
```
