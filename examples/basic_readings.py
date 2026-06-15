"""Basic sensor readout example for the LTR-381RGB-01.

This script demonstrates the default configuration of the driver and prints
values for every read-only property. Adjust the I2C bus ID and pin numbers to
match your board.
"""

from time import sleep_ms, ticks_ms
from machine import I2C, Pin  # type: ignore
from ltr381rgb.device import LTR381RGB


def main() -> None:
    """Take a single measurement and print all derived values."""

    # Update the bus ID and pins to match your MicroPython board.
    i2c = I2C(0)
    sensor = LTR381RGB(i2c)

    part_id, revision = sensor.part_revision
    print("🔍 LTR-381RGB detected: part=0x{:02X} revision=0x{:02X}".format(part_id, revision))

    print("⏱️ Integration time bits:", hex(sensor.integration_time))
    print("⏲️ Integration time (ms):", sensor.integration_time_ms)
    print("📈 Measurement rate bits:", hex(sensor.measurement_rate))
    print("🕒 Measurement period (ms):", sensor.measurement_period_ms)
    print("🎚️ Gain bits:", hex(sensor.gain))

    if not sensor.is_data_ready:
        print("⏳ Waiting for the first measurement...")
        while not sensor.is_data_ready:
            sleep_ms(10)

    raw_ir, raw_green, raw_red, raw_blue = sensor.raw_channels
    print("📡 Raw channels (IR, G, R, B):", raw_ir, raw_green, raw_red, raw_blue)

    print("🌿 Ambient (green) counts:", sensor.ambient_light)
    print("🎨 RGB counts (R, G, B):", sensor.rgb_color)
    print("🌈 Ambient snapshot:", sensor.ambient_rgb_ir)
    print("🌌 IR-only counts:", sensor.ir_light)
    print("🎯 Approximate color:", sensor.approximate_color)

    print("💡 Estimated lux:", sensor.lux)
    print("🌡️ Estimated color temperature (K):", sensor.color_temperature)

    corrected_lux = sensor.lux_from_raw(raw_green, raw_ir, window_factor=0.95)
    print("🔧 Lux with window factor=0.95:", corrected_lux)

    manual_cct = sensor.color_temperature_from_raw(raw_red, raw_green, raw_blue)
    print("🧪 Manual correlated color temperature (K):", manual_cct)

    sensor.disable()
    print("😴 Sensor disabled for power saving. Re-enabling in ALS-only mode...")
    sensor.enable(color_mode=False)
    print("✅ Data ready after re-enable:", sensor.is_data_ready)
    start_time = ticks_ms()

    while not sensor.is_data_ready:
        sleep_ms(10)

    elapsed_time = ticks_ms() - start_time
    print(f"✅ Data ready after {elapsed_time} ms.")

if __name__ == "__main__":
    main()
