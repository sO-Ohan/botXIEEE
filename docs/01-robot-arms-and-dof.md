# 1. What is a Robotic Arm? What is a DOF?

## Robotic arms

A **robotic arm** (formally a *serial manipulator*) is a chain of rigid
bodies — **links** — connected by **joints**, with one end fixed (the
**base**) and a tool at the other end (the **end effector**, here a claw).
Each joint is driven by an actuator; in our arm, every actuator is a hobby
servo motor.

It's called a *serial* manipulator because the links form one serial chain:
base → shoulder → elbow → wrist → gripper. Move any joint and everything
after it in the chain moves too. That single fact drives all the math.

## Degrees of freedom (DOF)

A **degree of freedom** is one independent way the mechanism can move.
Each single-axis joint contributes exactly one DOF. Joints come in two
flavors we care about:

- **Revolute** — rotates about an axis (all 5 arm joints).
- **Prismatic** — slides along an axis (our gripper fingers).

A free rigid body in space has 6 DOF: 3 translations (x, y, z) and
3 rotations (roll, pitch, yaw). So a manipulator needs **at least 6 joints**
to place its tool at *any* position in *any* orientation inside its
workspace.

## Our arm: "6 DOF" — but read the fine print

| # | Joint | Type | Motion | PCA9685 channel |
|---|-------|------|--------|-----------------|
| 1 | Base (waist) | revolute | yaw — pans the whole arm | 0 |
| 2 | Shoulder | revolute | pitch — highest torque load | 1 |
| 3 | Elbow | revolute | pitch | 2 |
| 4 | Wrist pitch | revolute | pitch — tilts the claw | 3 |
| 5 | Wrist roll | revolute | roll — spins the claw | 4 |
| 6 | Gripper | prismatic (via gears) | open/close, ~55 mm | 5 |

Kits like this are marketed as "6-DOF" by counting the gripper. But the
gripper doesn't move the tool through space — it only grasps. For
*positioning*, this is a **5-DOF arm**: it can reach positions freely, but
cannot achieve every orientation at every position (it's missing a second
wrist axis). You'll meet this again in the MoveIt chapter, where we
configure the IK solver as **position-only** for exactly this reason.

## Forward and inverse kinematics

- **Forward kinematics (FK):** given all joint angles, where is the tool?
  Straightforward — multiply the chain's transforms together. Always has
  exactly one answer.
- **Inverse kinematics (IK):** given a desired tool pose, what joint angles
  produce it? Hard — may have many solutions (elbow-up vs elbow-down), one,
  or none (out of reach). This is what MoveIt solves for us when we drag
  the interactive marker in RViz.

The description of link lengths and joint axes that both FK and IK need is
exactly what the **URDF** file provides (chapter 4).

## Workspace

The **workspace** is the set of points the tool can reach. Ours is roughly
a half-dome around the base: base yaw sweeps ±90°, and the
shoulder–elbow–wrist chain (~105 + 98 + 55 mm plus the gripper) sets the
reach radius to about 35 cm. MoveIt refuses plans to targets outside it —
a good live demo for class.

---
**Next:** [Hardware & electronics →](02-hardware-and-electronics.md)
