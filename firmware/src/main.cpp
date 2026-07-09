// botX arm firmware
// -----------------
// The ESP32 is a *dumb, safe* servo bridge: all intelligence (IK, planning,
// calibration, limits) lives on the ROS 2 side. The firmware only:
//   1. accepts absolute pulse-width targets over USB serial (ASCII lines),
//   2. slew-rate-limits motion so the aluminum arm never snaps,
//   3. clamps every pulse to a hard safety window.
//
// Protocol (newline-terminated ASCII, easy to type by hand in a monitor):
//   T <us0> <us1> <us2> <us3> <us4> <us5>   set all 6 targets (microseconds)
//   S <ch> <us>                             set one channel target
//   V <us_per_s>                            set slew speed
//   E <0|1>                                 disable/enable outputs (0 = limp)
//   Q                                       print current pulse values
//   PING                                    replies "PONG botx-fw 1.0"
//
// Servos stay unpowered (no PWM pulses) until the first T/S command arrives,
// so plugging in power never makes the arm jump.

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#include "config.h"

Adafruit_PWMServoDriver pwm(PCA9685_ADDR);

static float currentUs[NUM_SERVOS];   // where each servo is being commanded now
static float targetUs[NUM_SERVOS];    // where we want it to end up
static bool attached[NUM_SERVOS];     // channel has received a target at least once
static bool outputsEnabled = true;
static int speedUsPerS = DEFAULT_SPEED_US_S;

static char lineBuf[LINE_BUF_LEN];
static size_t lineLen = 0;

static int clampPulse(long us) {
  if (us < PULSE_MIN_US) return PULSE_MIN_US;
  if (us > PULSE_MAX_US) return PULSE_MAX_US;
  return (int)us;
}

static void setTarget(int ch, long us) {
  if (ch < 0 || ch >= NUM_SERVOS) return;
  targetUs[ch] = clampPulse(us);
  if (!attached[ch]) {
    // First command for this channel: no known position to slew from, so
    // start the ramp at the target itself (servo eases there on its own).
    currentUs[ch] = targetUs[ch];
    attached[ch] = true;
  }
}

static void handleLine(char *line) {
  // strtok-based parsing: cheap and adequate for a 6-field line
  char *cmd = strtok(line, " \r");
  if (!cmd) return;

  if (strcmp(cmd, "T") == 0) {
    for (int ch = 0; ch < NUM_SERVOS; ++ch) {
      char *tok = strtok(nullptr, " \r");
      if (!tok) { Serial.println("ERR T needs 6 values"); return; }
      setTarget(ch, atol(tok));
    }
    Serial.println("OK");
  } else if (strcmp(cmd, "S") == 0) {
    char *chTok = strtok(nullptr, " \r");
    char *usTok = strtok(nullptr, " \r");
    if (!chTok || !usTok) { Serial.println("ERR S <ch> <us>"); return; }
    setTarget(atoi(chTok), atol(usTok));
    Serial.println("OK");
  } else if (strcmp(cmd, "V") == 0) {
    char *tok = strtok(nullptr, " \r");
    if (!tok) { Serial.println("ERR V <us_per_s>"); return; }
    speedUsPerS = constrain(atoi(tok), 50, 4000);
    Serial.println("OK");
  } else if (strcmp(cmd, "E") == 0) {
    char *tok = strtok(nullptr, " \r");
    outputsEnabled = tok && atoi(tok) != 0;
    if (!outputsEnabled) {
      for (int ch = 0; ch < NUM_SERVOS; ++ch) {
        pwm.setPWM(ch, 0, 0);          // stop pulses -> servo goes limp
        attached[ch] = false;
      }
    }
    Serial.println("OK");
  } else if (strcmp(cmd, "Q") == 0) {
    Serial.print("POS");
    for (int ch = 0; ch < NUM_SERVOS; ++ch) {
      Serial.print(' ');
      Serial.print(attached[ch] ? (int)currentUs[ch] : -1);
    }
    Serial.println();
  } else if (strcmp(cmd, "PING") == 0) {
    Serial.println("PONG botx-fw 1.0");
  } else {
    Serial.println("ERR unknown command");
  }
}

static void pollSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      handleLine(lineBuf);
      lineLen = 0;
    } else if (lineLen < LINE_BUF_LEN - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineLen = 0;  // overlong garbage line: drop it
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);  // tune if measured 50Hz is off
  pwm.setPWMFreq(SERVO_PWM_HZ);

  for (int ch = 0; ch < NUM_SERVOS; ++ch) {
    attached[ch] = false;
    pwm.setPWM(ch, 0, 0);  // outputs off until first command
  }
  Serial.println("READY botx-fw 1.0");
}

void loop() {
  pollSerial();

  // slew loop: move currentUs toward targetUs at most maxStep per tick
  static unsigned long lastTick = 0;
  unsigned long now = millis();
  if (now - lastTick >= 1000UL / UPDATE_HZ) {
    lastTick = now;
    const float maxStep = (float)speedUsPerS / UPDATE_HZ;
    for (int ch = 0; ch < NUM_SERVOS; ++ch) {
      if (!attached[ch] || !outputsEnabled) continue;
      float diff = targetUs[ch] - currentUs[ch];
      if (diff > maxStep) diff = maxStep;
      if (diff < -maxStep) diff = -maxStep;
      currentUs[ch] += diff;
      pwm.writeMicroseconds(ch, (int)currentUs[ch]);
    }
  }
}
