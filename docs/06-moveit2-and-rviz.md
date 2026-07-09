# 6. MoveIt 2 & RViz

## What MoveIt 2 does

Given "put the tool THERE", MoveIt:

1. solves **IK** → joint angles for the target,
2. **plans** a collision-free joint-space path (OMPL / RRTConnect),
3. **time-parameterizes** it (velocity/acceleration limits from
   `joint_limits.yaml`),
4. **executes** it by streaming the trajectory to a controller — ours is
   the `FollowJointTrajectory` action server in `botx_driver`.

## URDF vs SRDF

The URDF says what the robot *is*; the **SRDF** (`config/botx.srdf`) says
how to *use* it:

- **Planning groups:** `arm` (the 5-joint chain `base_link → tool0`) and
  `gripper` (just `gripper_joint`).
- **Named states:** `home`, `ready` (arm), `open`, `closed` (gripper) —
  selectable in RViz's goal-state dropdown.
- **Collision matrix:** which link pairs to skip checking (adjacent links,
  parts that can never touch). Speeds up planning and kills false alarms.

## The 5-DOF catch (exam question material)

With only 5 positioning joints the arm **cannot hit an arbitrary 6-D pose**
(position *and* orientation). A full-pose IK solver would fail almost every
request. So `kinematics.yaml` sets:

```yaml
arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  position_only_ik: true
```

Drag the marker anywhere reachable and MoveIt finds joint angles that put
the **tool tip at that position**, letting orientation fall where it may.

## Run it

```bash
ros2 launch botx_moveit_config demo.launch.py
# without the ESP32 plugged in it says "SIMULATION mode" and works anyway
```

In RViz (MotionPlanning panel):

1. Drag the interactive marker on the tool tip to a goal.
2. **Plan** — watch the animated ghost trajectory.
3. **Execute** — watch RViz *and the real arm* follow it.
4. Try Goal State → `ready`, `home`; switch group to `gripper` and plan
   `open` → `closed`.

## How execution reaches the servos

```
RViz "Execute" → move_group → moveit_simple_controller_manager
  → action: /arm_controller/follow_joint_trajectory   (botx_driver)
  → driver interpolates the trajectory at 30 Hz
  → serial "T 1500 1622 ..." → ESP32 → PCA9685 → servos
```

`config/moveit_controllers.yaml` is the file that binds MoveIt to those
action names — it's 30 lines; read it once and controller config stops
being magic.

## Calibrating the real arm to match RViz

Servo horns never sit exactly at center. Per joint, in
`botx_driver/config/servo_calibration.yaml`:

1. jog the joint positive — if the hardware moves opposite to RViz, flip
   the sign of `us_per_unit`;
2. at 0 rad, if hardware is offset, adjust `center_us`;
3. tighten `min_us`/`max_us` before the mechanical stops.

Rebuild is not needed (config is read at node start; restart the launch).

---
**Next:** [Gamepad teleoperation →](07-gamepad-teleop.md)
