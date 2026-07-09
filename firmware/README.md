# botX Firmware (ESP32 + PCA9685)

Dumb-and-safe servo bridge: receives pulse-width targets over USB serial,
smooths them, and drives the PCA9685. All intelligence lives in ROS 2.

## Build & flash

```bash
cd firmware
pio run -t upload          # auto-detects the ESP32 port
pio device monitor         # 115200 baud
```

## Try it by hand (no ROS needed)

Open the monitor and type:

```
PING                                  -> PONG botx-fw 1.0
T 1500 1500 1500 1500 1500 1500       -> all six servos to center
S 0 1800                              -> base servo only
V 400                                 -> slow everything down
E 0                                   -> release all servos (limp)
Q                                     -> print current pulse values
```

Protocol details are documented at the top of `src/main.cpp`.

## Safety behavior

- No pulses are generated until the first target command, so powering the
  servo rail never makes the arm jump.
- Every pulse is clamped to 500-2500 µs in hardware-guard fashion;
  per-joint travel limits are enforced on the ROS side
  (`botx_driver/config/servo_calibration.yaml`).
- Motion is slew-rate limited (default ~80°/s, change with `V`).
