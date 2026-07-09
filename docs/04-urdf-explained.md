# 4. URDF — Describing a Robot

## What is URDF?

**URDF (Unified Robot Description Format)** is an XML file that tells ROS
what your robot *is*: its links, joints, geometry, and physical properties.
Every tool downstream — TF, RViz, MoveIt, Gazebo — reads this one model.

Two building blocks:

```xml
<link name="upper_arm">          <!-- a rigid body -->
  <visual> ... </visual>         <!-- what it looks like -->
  <collision> ... </collision>   <!-- shape used for collision checking -->
  <inertial> ... </inertial>     <!-- mass, for simulation -->
</link>

<joint name="elbow_pitch_joint" type="revolute">  <!-- connects two links -->
  <parent link="upper_arm"/>
  <child  link="forearm"/>
  <origin xyz="0 0 0.105"/>      <!-- where the joint sits on the parent -->
  <axis   xyz="0 1 0"/>          <!-- rotation axis (Y = pitch) -->
  <limit lower="-1.57" upper="1.57" effort="1.0" velocity="2.0"/>
</joint>
```

A URDF is a **tree**: one root link (`base_link`), every other link hangs
off exactly one joint. Ours:

```
base_link → shoulder_mount → upper_arm → forearm → wrist → roll_flange
                                                             → gripper_base → finger_left
                                                                            → finger_right
                                                                            → tool0
```

## What is xacro?

Raw URDF gets repetitive fast. **xacro** adds variables and macros:

```xml
<xacro:property name="upper_arm_length" value="0.105"/>
<xacro:macro name="arm_segment" params="name length mass"> ... </xacro:macro>
```

Our model (`botx_description/urdf/botx_arm.urdf.xacro`) puts **every link
length in one property block at the top** — measure your arm
(axis-to-axis!) and edit those numbers; nothing else needs to change.

## Did we find one on the internet?

We looked. ROT3U/SainSmart-style kits are popular, but the GitHub projects
around them ship control code, not a proper URDF — and kits vary in exact
bracket stacking anyway. So this repo carries its own hand-written xacro.
Writing one is genuinely the better lesson: ~200 readable lines, and now
you know what every line of any robot's URDF means.

## Details worth teaching

- **`tool0`** — a massless "tool frame" between the fingertips. IK targets
  this frame, not a physical part. Industrial robots use the same idiom.
- **`<mimic>`** — the claw has ONE servo but two fingers. `gripper_joint`
  is the real (prismatic) joint; `gripper_mirror_joint` copies it so the
  visualization shows both fingers moving.
- **Units:** meters and radians, always. Servo pulse µs never appear in
  the URDF — that mapping lives in the driver's calibration file.
- **Joint limits ±90°** match the servos' 180° travel, with 0 rad at the
  1500 µs servo center.

## See it

```bash
distrobox enter ubuntu
cd ~/Documents/botXIEEE/ros2_ws && source install/setup.bash
ros2 launch botx_description display.launch.py
```

`joint_state_publisher_gui` gives you a slider per joint; RViz renders the
model and its TF frames. This is the whole "URDF → TF → RViz" pipeline in
one window — no MoveIt, no hardware.

Validate after editing:

```bash
xacro src/botx_description/urdf/botx_arm.urdf.xacro > /tmp/botx.urdf
check_urdf /tmp/botx.urdf
```

---
**Next:** [The ROS 2 workspace →](05-ros2-workspace.md)
