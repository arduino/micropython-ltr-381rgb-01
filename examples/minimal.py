"""Basic sensor readout example for the LTR-381RGB-01.

This script demonstrates the default configuration of the driver and prints
values for every read-only property. Adjust the I2C bus ID and pin numbers to
match your board.
"""

import time
from machine import I2C, Pin  # type: ignore
from ltr381rgb.device import LTR381RGB


def main() -> None:
    """Take a single measurement and print all derived values."""

    # Update the bus ID and pins to match your MicroPython board.
    i2c = I2C(0)
    sensor = LTR381RGB(i2c)

    part_id, revision = sensor.part_revision
    print("🔍 LTR-381RGB detected: part=0x{:02X} revision=0x{:02X}".format(part_id, revision))

    while True:
        if not sensor.is_data_ready:
            time.sleep_ms(5)

        data = sensor.ambient_rgb_ir
        print("🌿 Ambient light:", data["ambient"])
        print("🎨 RGB value (R, G, B):", data["rgb"])
        print("🌌 Infrared:", data["ir"])

if __name__ == "__main__":
    main()
