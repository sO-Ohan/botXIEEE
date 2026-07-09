# 10. Terminal Keyboard Controller (TUI)

A third way to drive the arm — no gamepad, no RViz, just a terminal:

```bash
# terminal 1 — the driver (either of these)
ros2 launch botx_moveit_config demo.launch.py
ros2 launch botx_driver driver.launch.py

# terminal 2 — the controller
ros2 run botx_tui arm_tui
```

```
══════════════════════════ botX  ARM  CONTROL ══════════════════════════
  ● DRIVER ONLINE     step: 1.1°/press   [+/-] change

  ▶ 1 Base yaw     [█████████████┼────────────]   +0.0°
                    -90..+90°
    2 Shoulder     [█████████████┼────────────]   +0.0°
    3 Elbow        [█████████████┼────────────]   +0.0°
    4 Wrist pitch  [█████████████┼────────────]   +0.0°
    5 Wrist roll   [█████████████┼────────────]   +0.0°
    6 Gripper      [─────────────┼────────────]    0.0mm
 ────────────────────────────────────────────────────────────────────────
   ↑↓/kj select   ←→/ad move   1-6 jump   o/c gripper
   +/- step   h home   space stop   q quit
```

## Keys

| Key | Action |
|---|---|
| `↑`/`↓` or `k`/`j` | select joint |
| `1`–`6` | jump straight to a joint |
| `←`/`→` or `a`/`d` | move the selected joint (hold for continuous motion) |
| `+` / `-` | step size per keypress (0.3° / 1.1° / 2.9°) |
| `o` / `c` | gripper open / close |
| `h` | smooth-return to home pose (calls `/go_home`) |
| `space` | stop |
| `q` / `Esc` | quit |

## How it works (one more architecture lesson)

Each keypress publishes a **one-shot position nudge** —
`control_msgs/JointJog` with a `displacements` entry — to the same
`/joint_jog` topic the gamepad uses (the gamepad fills `velocities`
instead; the driver understands both). Holding a key rides the OS
key-repeat, so motion is continuous while held and stops *instantly* on
release — no timers, no key-up events (terminals don't have them).

The gauges are not an echo of what you pressed: the TUI subscribes to
`/joint_states` and draws what the **driver** reports, after clamping to
joint limits. If the driver is down, the header says `○ DRIVER OFFLINE`
and keys go nowhere. Display truth, not wishes.

Because everything funnels through the driver, the TUI coexists with the
gamepad, RViz, and MoveIt — jog with the keyboard, then plan from
wherever the arm ended up. It's also plain stdlib `curses`: zero extra
dependencies, ~250 readable lines
(`ros2_ws/src/botx_tui/botx_tui/arm_tui.py`).

Tip: it runs fine over SSH — you can drive the arm from another machine
on the network with nothing but a terminal.

---
**Back to:** [Class demo script](08-class-demo-script.md) ·
[Troubleshooting](09-troubleshooting.md)
