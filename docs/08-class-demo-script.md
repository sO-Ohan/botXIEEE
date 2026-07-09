# 8. Class Demo Script (~45 min lesson plan)

Pre-flight (before students arrive):

- [ ] Close any old ROS terminals (especially other arm workspaces —
      stray `/joint_states` publishers corrupt the demo; see ch. 9).
- [ ] ESP32 on USB (`ls /dev/ttyUSB*`), servo PSU on, gamepad plugged in.
- [ ] `distrobox enter ubuntu`, workspace built and sourced.
- [ ] Dry-run `demo.launch.py` once.

## Act 1 — Concepts (10 min, slides/whiteboard)

1. Serial manipulator: links + joints, base → end effector. Point at the
   physical arm while naming each joint. *(ch. 1)*
2. DOF: one per joint; free body needs 6; our arm = 5 positioning + gripper.
3. FK vs IK in one sentence each.

## Act 2 — Hardware (5 min, pass the arm around)

4. Trace the signal path: PC → USB → ESP32 → I2C → PCA9685 → PWM → servo.
5. Show the two power rails; explain why servos get their own supply. *(ch. 2)*

**Checkpoint A — firmware, no ROS:**
```
pio device monitor
> T 1500 1500 1500 1500 1500 1500      ← the arm centers, smoothly
> E 0                                  ← arm goes limp; hand it around again
```

## Act 3 — URDF (10 min)

6. Open `botx_arm.urdf.xacro`; show one `<link>`, one `<joint>`, the
   property block with the measured lengths.

**Checkpoint B — model only:**
```
ros2 launch botx_description display.launch.py
```
Move each slider; students call out which physical joint it corresponds
to. Show TF frames. *(ch. 4)*

## Act 4 — ROS 2 + MoveIt 2 (15 min)

7. Two-minute node/topic/action tour: `rqt_graph`, `ros2 topic echo /joint_states --once`. *(ch. 5)*

**Checkpoint C — the money demo:**
```
ros2 launch botx_moveit_config demo.launch.py
```
8. Drag the marker → **Plan** (ghost animation) → **Execute** (real arm
   follows RViz).
9. Plan to an unreachable point → planning fails → workspace concept lands.
10. Gripper group: `open` → `closed`.
11. Mention the 5-DOF position-only-IK fine print. *(ch. 6)*

## Act 5 — Teleop (5 min)

**Checkpoint D:**
```
ros2 launch botx_teleop teleop.launch.py
```
12. Drive with the sticks; press Start to auto-home. Explain
    Joy → JointJog → driver, and the 0.5 s dead-man freeze. *(ch. 7)*
13. Finale: jog the arm somewhere awkward with the pad, then have MoveIt
    plan home from there — teleop and autonomy sharing one state.

## Q&A ammunition

- "Why not compute IK on the ESP32?" → ch. 3 design philosophy.
- "Is it really 6-DOF?" → ch. 1 fine print.
- "What if I unplug the arm mid-demo?" → driver switches to simulation;
  unplug it live if you're feeling brave.
