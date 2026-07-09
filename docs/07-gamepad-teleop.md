# 7. Gamepad Teleoperation (Fantech controller)

## The pipeline

```
Fantech pad → Linux joystick driver (/dev/input/js0)
           → joy_node                    (sensor_msgs/Joy: raw axes+buttons)
           → botx_teleop/joy_teleop      (mapping + deadzone)
           → /joint_jog                  (control_msgs/JointJog: joint velocities)
           → botx_driver                 (integrates velocity → position, streams to ESP32)
```

Design point worth teaching: the teleop node is **stateless** — it only
converts stick deflection to joint *velocities*. The driver integrates
them into positions and enforces limits. If the pad unplugs or the teleop
node dies, jog messages stop and the driver freezes the arm within 0.5 s.
Safety by architecture, not by exception handling.

## Run it

```bash
# terminal 1 — MoveIt demo (or the bare driver)
ros2 launch botx_moveit_config demo.launch.py

# terminal 2 — teleop
ros2 launch botx_teleop teleop.launch.py
```

## Default mapping (`botx_teleop/config/fantech.yaml`)

| Control | Action |
|---|---|
| Left stick ←/→ | base yaw |
| Left stick ↑/↓ | shoulder pitch |
| Right stick ↑/↓ | elbow pitch |
| Right stick ←/→ | wrist roll |
| D-pad ↑/↓ | wrist pitch |
| RB / LB | gripper open / close |
| Start | go home (calls `/go_home`) |

## If your pad maps differently

Fantech pads usually enumerate as XInput-style gamepads; some have a
mode switch (check the "Analog"/mode button). To verify:

```bash
ros2 topic echo /joy
```

Wiggle one stick at a time, note which array index changes, then edit the
`axis:` numbers in `config/fantech.yaml`. Flip a `scale:` sign to invert
a direction. Restart the teleop launch — no rebuild needed.

## Teleop and MoveIt coexist

Both feed the same driver: jog with the pad, then plan with MoveIt from
wherever you left the arm — MoveIt always plans from the current
`/joint_states`. (During trajectory execution the driver ignores jog input
on the moving joints, so they can't fight.)

---
**Next:** [Class demo script →](08-class-demo-script.md)
