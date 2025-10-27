# MicroPython LTR-381RGB-01 Driver

This project provides a MicroPython driver for Lite-On's LTR-381RGB-01
ambient light and color sensor. The driver handles low-level I²C register
transactions, exposes configuration knobs for integration time, measurement
cadence, and gain, and supports the on-chip interrupt thresholds described in
the datasheet.

## Features

- ✅ 20-bit raw channel reads for IR, green (ALS), red, and blue photodiodes.
- ✅ Integration time and measurement rate helpers that track their actual
  timings in milliseconds.
- ✅ Gain configuration with datasheet-aligned bit-fields.
- ✅ Interrupt threshold and persistence configuration including per-channel
  source selection.
- ✅ Convenience helpers for checking data readiness and rebooting the sensor.
- ✅ High-level properties for ambient light and RGB color retrieval, including a combined helper.
- ✅ Lux and correlated color temperature helpers built from a single raw sample.
- ✅ Compatibility property matching Adafruit's LTR329 driver (`ir_light`).
- ✅ Basic color classification helper that bins raw RGB into familiar hue names.

## Quick start

```python
from machine import I2C, Pin
from ltr381rgb import LTR381RGB, IntegrationTime, MeasurementRate, Gain

i2c = I2C(0, scl=Pin(21), sda=Pin(20))
sensor = LTR381RGB(i2c)

# Tune measurement parameters if needed
sensor.integration_time = IntegrationTime.MS400
sensor.measurement_rate = MeasurementRate.MS500
sensor.gain = Gain.X3

# Fetch a fresh set of 20-bit readings in (IR, green, red, blue) order
ir, green, red, blue = sensor.raw_channels

# Or build a dict keyed by channel name on demand
channels = dict(zip(("ir", "green", "red", "blue"), sensor.raw_channels))
print(channels["green"])

# Quick ambient lux-style read (raw 20-bit ALS channel)
ambient = sensor.ambient_light

# Retrieve RGB tuple scaled to 0–255 ordered as (red, green, blue).
# The brightest channel in the current sample is normalized to 255.
rgb_8bit = sensor.rgb_color

# Or capture ambient and scaled RGB in one go
reading = sensor.ambient_rgb
ambient = reading["ambient"]  # raw 20-bit green count
rgb = reading["rgb"]          # per-sample normalized 0–255 tuple
ir = reading["ir"]            # raw IR count

# Convert the raw counts into lux (optionally pass calibration to `lux_from_raw`)
lux = sensor.lux
# calibrated_lux = sensor.lux_from_raw(green, ir, window_factor=1.1)

# Estimate correlated color temperature (Kelvin). Matrix parameter enables calibration if needed.
cct = sensor.color_temperature
# calibrated_cct = sensor.color_temperature_from_raw(red, green, blue, matrix=my_matrix)

# Adafruit LTR329 compatibility accessor for the IR-only channel
ir_only = sensor.ir_light

# Grab a coarse color name such as "cyan" or "violet"
color_name = sensor.approximate_color
```

> **Note:** When running the examples or quick-start code directly from this
> repository, ensure ``src`` is on ``sys.path`` (the included example scripts do
> this automatically). When deploying to a board, copy the contents of
> ``src/ltr381rgb`` into your MicroPython filesystem.

## Examples

- `examples/basic_readings.py` – Minimal script that reads every measurement
  property, prints approximate color/lux/CCT, and demonstrates toggling ALS-only mode.
- `examples/advanced_configuration.py` – Exercises configuration setters,
  manual lux/CCT helpers, interrupt thresholds, and reset/reboot flows.

Both scripts assume a MicroPython environment; update the I²C bus ID and pins to
match your board before running them.

## Module overview

- `src/ltr381rgb/constants.py` – Symbolic register addresses and bit masks.
- `src/ltr381rgb/enums.py` – Enumerations for integration time, measurement rate, and gain.
- `src/ltr381rgb/device.py` – The `LTR381RGB` driver implementation.
- `src/ltr381rgb/errors.py` – Exception hierarchy shared across the package.

## Implementation notes

- Channel results are 20-bit little-endian values; the driver masks and packs
  them into Python integers.
- The ``rgb_color`` and ``ambient_rgb['rgb']`` values scale raw red/green/blue
  readings so the brightest channel in the current sample maps to 255,
  yielding an 8-bit tuple (0–255). Use ``ambient_light`` or ``raw_channels``
  when you need the original 20-bit counts.
- The driver automatically enforces the datasheet requirement that the
  measurement rate be equal to or slower than the configured integration time.
- Helper properties expose the effective integration and measurement periods in
  milliseconds for easier timeout calculations.
- Lux conversion follows the datasheet guidance using the green and IR channels plus
  gain/integration scaling. Supply a custom window factor or IR coefficient when
  working behind coated glass.
- Color temperature estimation uses a configurable RGB→XYZ matrix (defaults to a
  generic approximation) and McCamy's formula. Calibrate the matrix for the most
  accurate CCT on your optical stack.

## Datasheet

Refer to the [LTR-381RGB-01 official datasheet](https://optoelectronics.liteon.com/upload/download/DS86-2018-0007/LTR-381RGB-01_Final_DS_V1.8.PDF)
for detailed electrical characteristics, register descriptions, and timing
constraints.
