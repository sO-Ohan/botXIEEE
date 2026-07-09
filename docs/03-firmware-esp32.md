# 3. The ESP32 Firmware

## Design philosophy: the firmware is *dumb on purpose*

A classic beginner mistake is putting inverse kinematics on the
microcontroller. We do the opposite — a clean split:

| Layer | Responsibility |
|---|---|
| ROS 2 on the PC | kinematics, planning, calibration, joint limits, teleop |
| ESP32 firmware | receive pulse targets, smooth them, clamp them, output PWM |

The microcontroller becomes a *servo modem*. It can be replaced, the
protocol can be typed by hand, and nothing on it ever needs retuning when
the robot model changes. (A micro-ROS client on the ESP32 is a nice
upgrade path later; a plain serial protocol is simpler to teach and debug.)

## The protocol (ASCII lines over USB serial, 115200 baud)

| Command | Meaning |
|---|---|
| `T us0 us1 us2 us3 us4 us5` | set all 6 servo pulse targets in µs |
| `S ch us` | set one channel |
| `V us_per_s` | slew speed (default 900 ≈ 80°/s) |
| `E 0` / `E 1` | disable (limp) / enable outputs |
| `Q` | report current pulses |
| `PING` | replies `PONG botx-fw 1.0` |

## Safety behavior baked in

- **No pulses until first command** — powering the arm never makes it jump.
- **Slew-rate limiting** — targets are ramped, never stepped, so a buggy
  command can't whip the aluminum around.
- **Hard pulse clamp** (500–2500 µs) — last-line guard below the per-joint
  limits enforced in ROS.

## Flash it

```bash
cd firmware
pio run -t upload         # PlatformIO; auto-detects /dev/ttyUSB0
pio device monitor        # then type: PING  →  PONG botx-fw 1.0
```

## The one loop that matters

Every 20 ms the firmware moves each servo's *current* pulse toward its
*target* by at most `speed/50` µs, then writes it to the PCA9685:

```cpp
const float maxStep = (float)speedUsPerS / UPDATE_HZ;
float diff = targetUs[ch] - currentUs[ch];
if (diff >  maxStep) diff =  maxStep;
if (diff < -maxStep) diff = -maxStep;
currentUs[ch] += diff;
pwm.writeMicroseconds(ch, (int)currentUs[ch]);
```

That's the whole trick that turns jerky hobby servos into smooth motion.

## Try it with no ROS at all (great class moment)

```
pio device monitor
> T 1500 1500 1500 1500 1500 1500     # arm gently centers itself
> S 0 2000                            # base pans
> E 0                                 # arm goes limp
```

---
**Next:** [URDF — describing a robot →](04-urdf-explained.md)
