#pragma once

// ---------- wiring (matches the hardware doc) ----------
constexpr int PIN_I2C_SDA = 21;   // ESP32 GPIO21 -> PCA9685 SDA
constexpr int PIN_I2C_SCL = 22;   // ESP32 GPIO22 -> PCA9685 SCL
constexpr uint8_t PCA9685_ADDR = 0x40;  // default, all address jumpers open

// ---------- servos ----------
constexpr int NUM_SERVOS = 6;     // PCA9685 channels 0..5, base -> gripper
constexpr float SERVO_PWM_HZ = 50.0f;  // 20 ms frame, standard hobby servo

// Absolute pulse clamp. Per-joint limits live on the ROS side
// (servo_calibration.yaml); this is only a last-line hardware guard.
constexpr int PULSE_MIN_US = 500;
constexpr int PULSE_MAX_US = 2500;

// ---------- motion smoothing ----------
constexpr int UPDATE_HZ = 50;           // internal slew loop rate
constexpr int DEFAULT_SPEED_US_S = 900; // max pulse change per second
                                        // (~80 deg/s) - keeps moves gentle

// ---------- protocol ----------
constexpr unsigned long SERIAL_BAUD = 115200;
constexpr size_t LINE_BUF_LEN = 96;
