"""Advanced configuration example for the LTR-381RGB-01 sensor.

This script exercises the full public API including timing configuration,
threshold interrupts, and manual lux/CCT calculations. Run it on a
MicroPython board after adjusting the I2C pins to match your wiring.
"""

from time import sleep_ms, ticks_ms, ticks_diff
from machine import I2C

from ltr381rgb import LTR381RGB
from ltr381rgb import Gain, IntegrationTime, MeasurementRate
from ltr381rgb import LTR381RGBError, LTR381RGBTimeout


def wait_for_sample(sensor: LTR381RGB, timeout_ms: int = 1000) -> None:
    """Block until a fresh measurement is available."""

    start = ticks_ms()
    while not sensor.data_ready:
        if ticks_diff(ticks_ms(), start) >= timeout_ms:
            raise RuntimeError("Timed out waiting for measurement")
        sleep_ms(5)


def configure_sensor(i2c: I2C) -> None:
    """Showcase advanced API usage for the sensor."""

    sensor = LTR381RGB(i2c)

    print("⏱️ Initial integration bits:", hex(sensor.integration_time))
    print("📈 Initial measurement rate bits:", hex(sensor.measurement_rate))
    print("🎚️ Initial gain bits:", hex(sensor.gain))

    sensor.disable()
    print("😴 Sensor disabled for reconfiguration")

    sensor.integration_time = IntegrationTime.MS400
    sensor.measurement_rate = MeasurementRate.MS500
    sensor.gain = Gain.X3

    print("⏲️ Updated integration bits:", hex(sensor.integration_time))
    print("🕒 Updated integration time (ms):", sensor.integration_time_ms)
    print("📊 Updated measurement rate bits:", hex(sensor.measurement_rate))
    print("🧭 Updated measurement period (ms):", sensor.measurement_period_ms)
    print("🎛️ Updated gain bits:", hex(sensor.gain))

    sensor.enable(color_mode=True)
    print("🔁 Sensor re-enabled in full color mode")

    wait_for_sample(sensor)

    ir, green, red, blue = sensor.raw_channels
    print("📡 Configured raw channels (ir, green, red, blue):", ir, green, red, blue)

    print("🌿 Ambient light counts:", sensor.ambient_light)
    print("🎨 RGB tuple:", sensor.rgb_color)
    print("🌈 Ambient snapshot:", sensor.ambient_rgb_ir)
    print("🌌 IR-only counts:", sensor.ir_light)
    print("🎯 Approximate color:", sensor.approximate_color)

    estimated_lux = sensor.lux
    manual_lux = sensor.lux_from_raw(green, ir, gain_bits=sensor.gain, integration_bits=sensor.integration_time, window_factor=0.85)
    print("💡 Estimated lux (property):", estimated_lux)
    print("🛠️ Manual lux computation (window=0.85):", manual_lux)

    estimated_cct = sensor.color_temperature
    manual_cct = sensor.color_temperature_from_raw(red, green, blue)
    print("🌡️ Estimated CCT (K):", estimated_cct)
    print("🧪 Manual CCT (K):", manual_cct)

    low_threshold = 0x0800
    high_threshold = 0x50000
    sensor.thresholds = (low_threshold, high_threshold)
    print("🚦 Thresholds configured:", sensor.thresholds)

    sensor.configure_interrupts(enable=True, persist=4, source="green")
    print("🔔 Interrupts enabled on green channel with persist=4")

    part_id, revision = sensor.sensor_info
    print("🆔 Part information:", (part_id, revision))

    print("🔄 Rebooting sensor to apply a clean state...")
    sensor.reboot(timeout_ms=500)

    sensor.configure_interrupts(enable=False)
    print("🚫 Interrupts disabled")

    print("♻️ Demonstrating reset() call followed by enable()")
    sensor.reset()
    sensor.enable(color_mode=True)

    # Collect one more sample to confirm the device is operating after reset.
    wait_for_sample(sensor)
    print("📡 Post-reset raw channels (ir, green, red, blue):", sensor.raw_channels)

    sensor.disable()
    print("🏁 Sensor disabled at end of script")


def main() -> None:
    """Configure the sensor and handle any driver errors."""

    # Update the bus ID and pins to match your hardware setup.
    i2c = I2C(0)

    try:
        configure_sensor(i2c)
    except (LTR381RGBError, LTR381RGBTimeout) as exc:
        print("⚠️ Sensor reported an error:", exc)
    except RuntimeError as exc:
        print("❗ Runtime error:", exc)


if __name__ == "__main__":
    main()
