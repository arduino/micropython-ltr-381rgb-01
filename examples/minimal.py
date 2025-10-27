"""Basic sensor readout example for the LTR-381RGB-01.

This script demonstrates the default configuration of the driver and prints
values for every read-only property. Adjust the I2C bus ID and pin numbers to
match your board.
"""

import time

try:
    from machine import I2C, Pin  # type: ignore
except ImportError:  # pragma: no cover - CPython fallback for linting
    class I2C:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("machine.I2C is only available on MicroPython")

    class Pin:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("machine.Pin is only available on MicroPython")

from ltr381rgb.device import LTR381RGB


def main() -> None:
    """Take a single measurement and print all derived values."""

    # Update the bus ID and pins to match your MicroPython board.
    i2c = I2C(0)
    sensor = LTR381RGB(i2c)

    part_id, revision = sensor.part_revision
    print("LTR-381RGB detected: part=0x{:02X} revision=0x{:02X}".format(part_id, revision))

    while True:
        start_time = time.ticks_ms()

        if not sensor.is_data_ready:
            time.sleep_ms(5)

        print("Ambient light:", sensor.ambient_light)
        print("RGB value (R, G, B):", sensor.rgb_color)
        print("Combined values:", sensor.ambient_rgb_ir)
        print("Infrared:", sensor.ir_light)
        print("Approximate color:", sensor.approximate_color)
        print("Estimated lux:", sensor.lux)
        print("Estimated color temperature (K):", sensor.color_temperature)

        # Print FPS
        print("FPS:", 1000 / (time.ticks_ms() - start_time))

if __name__ == "__main__":
    main()
