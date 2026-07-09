# 2. Hardware & Electronics

## Mechanics

- **Chassis:** 2 mm hard aluminum alloy, black anodized; standardized
  interlocking brackets (multi-purpose, long-U, L, U-beam base).
- **Bearings:** metal flange bearings on the passive side of each joint —
  the servo spline drives one side, the bearing supports the other.
- **End effector:** parallel claw, one servo + spur gears, ~55 mm max opening.
- **Actuators:** 6× MG996R-class servos — metal gears, 4.8–7.2 V,
  ~9.4–11 kg·cm stall torque, standard 50 Hz PWM
  (500 µs ≈ 0°, 1500 µs ≈ 90°, 2500 µs ≈ 180°).

## Control electronics

Two chips, one job each:

- **ESP32** — runs the firmware; talks to the PC over USB serial and to the
  servo driver over I2C. Does *no* kinematics: all intelligence lives in ROS.
- **PCA9685** — 16-channel, 12-bit PWM generator. Generates six rock-steady
  50 Hz servo signals so the ESP32 never has to bit-bang PWM.

### Wiring

```
 PC ──USB──► ESP32                        6.0–7.2V high-current PSU
              │ 3V3  ──────► VCC  ┐          │ (≥10 A recommended)
              │ GND  ──────► GND  │ PCA9685  │
              │ GPIO21 ────► SDA  │          ▼
              │ GPIO22 ────► SCL  ┘        V+ / GND (screw terminal)
              │                              │
              └── logic side          power side ── channels 0–5 ──► servos
```

| ESP32 pin | PCA9685 pin | Purpose |
|---|---|---|
| 3V3 | VCC | logic power for the chip itself |
| GND | GND | common ground (shared with servo PSU!) |
| GPIO 21 | SDA | I2C data (default address 0x40) |
| GPIO 22 | SCL | I2C clock (400 kHz) |

| PCA9685 channel | Servo |
|---|---|
| 0 | Base yaw |
| 1 | Shoulder pitch |
| 2 | Elbow pitch |
| 3 | Wrist pitch |
| 4 | Wrist roll |
| 5 | Gripper |

## Power — the part that bites everyone

One MG996R can draw **1–1.5 A at stall**; six under load can spike past
**6–8 A**. Rules:

1. Servo power comes from a **dedicated supply** into the PCA9685 **V+**
   screw terminal — never from the ESP32's 5 V/3V3 pins, never from USB.
2. **VCC (logic) and V+ (servo power) are separate rails** on the PCA9685.
   VCC comes from the ESP32's 3V3 so the I2C levels match.
3. **Grounds must be common:** PSU ground, PCA9685 GND, ESP32 GND.
4. Symptoms of starving servos: ESP32 rebooting (brownout), servos
   twitching, WiFi dropping, "possessed arm" jitter. See troubleshooting.

---
**Next:** [The ESP32 firmware →](03-firmware-esp32.md)
