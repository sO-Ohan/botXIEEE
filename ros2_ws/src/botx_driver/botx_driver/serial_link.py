"""Thin, resilient wrapper around the USB serial connection to the ESP32.

The wire protocol is deliberately human-readable ASCII so it can be
exercised by hand with `minicom` / `screen` while teaching:

    T <us0> <us1> <us2> <us3> <us4> <us5>\n   set all 6 servo targets (microseconds)
    V <us_per_s>\n                            set firmware slew speed
    PING\n                                    firmware answers "PONG ..."

The firmware does its own smoothing (slew-rate limiting), so this side
just streams absolute targets at a modest rate.
"""
import serial


class SerialLink:
    def __init__(self, logger):
        self._log = logger
        self._ser = None
        self.port = None

    @property
    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def open(self, port: str, baud: int) -> bool:
        self.close()
        try:
            self._ser = serial.Serial(port, baud, timeout=0.05, write_timeout=0.2)
            self.port = port
            self._log.info(f"Connected to ESP32 on {port} @ {baud} baud")
            return True
        except (serial.SerialException, OSError) as e:
            self._ser = None
            self._log.debug(f"Could not open {port}: {e}")
            return False

    def write_line(self, line: str) -> bool:
        if not self.is_open:
            return False
        try:
            self._ser.write((line + "\n").encode("ascii"))
            return True
        except (serial.SerialException, OSError) as e:
            self._log.warn(f"Serial write failed ({e}); switching to simulation mode")
            self.close()
            return False

    def close(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except (serial.SerialException, OSError):
                pass
            self._ser = None
