"""Device level API for interacting with the LTR-381RGB-01 sensor."""

import time

from .constants import (
    CHANNEL_REGISTER_SIZE,
    DATA_20BIT_MASK,
    DATA_HIGH_NIBBLE_MASK,
    DEFAULT_I2C_ADDRESS,
    EXPECTED_PART_ID,
    GAIN_MASK,
    INT_CFG_ENABLE,
    INT_CFG_SOURCE_MASK,
    INT_PST_PERSIST_MASK,
    MAIN_CTRL_ALS_ENABLE,
    MAIN_CTRL_CS_MODE,
    MAIN_CTRL_SW_RESET,
    MAIN_STATUS_DATA_NEW,
    MEAS_RATE_MASK,
    MEAS_RESOLUTION_MASK,
    REG_ALS_CS_GAIN,
    REG_ALS_CS_MEAS_RATE,
    REG_ALS_THRESH_LOW_L,
    REG_ALS_THRESH_UP_L,
    REG_CS_DATA_BLUE,
    REG_CS_DATA_GREEN,
    REG_CS_DATA_IR,
    REG_CS_DATA_RED,
    REG_INT_CFG,
    REG_INT_PST,
    REG_MAIN_CTRL,
    REG_MAIN_STATUS,
    REG_PART_ID,
    RGB_MAX_VALUE,
)
from .enums import Gain, IntegrationTime, MeasurementRate
from .errors import LTR381RGBError, LTR381RGBTimeout

try:  # pragma: no cover - compatibility helper for CPython tooling
    from micropython import const
except ImportError:  # pragma: no cover - used outside MicroPython for linting
    def const(value):  # type: ignore
        return value


try:
    ticks_ms = time.ticks_ms
    ticks_diff = time.ticks_diff
    ticks_add = time.ticks_add
except AttributeError:  # pragma: no cover - CPython fallback for development
    def ticks_ms() -> int:  # type: ignore
        return int(time.time() * 1000)

    def ticks_diff(current: int, previous: int) -> int:  # type: ignore
        return current - previous

    def ticks_add(ticks: int, delta: int) -> int:  # type: ignore
        return ticks + delta


_INTEGRATION_MS = {
    IntegrationTime.MS400: 400,
    IntegrationTime.MS200: 200,
    IntegrationTime.MS100: 100,
    IntegrationTime.MS50: 50,
    IntegrationTime.MS25: 25,
}

_MEASUREMENT_OPTIONS = (
    (MeasurementRate.MS25, 25),
    (MeasurementRate.MS50, 50),
    (MeasurementRate.MS100, 100),
    (MeasurementRate.MS200, 200),
    (MeasurementRate.MS500, 500),
    (MeasurementRate.MS1000, 1000),
    (MeasurementRate.MS2000, 2000),
)

_MEASUREMENT_MS = {bits: ms for bits, ms in _MEASUREMENT_OPTIONS}

_INT_SOURCE_BITS = {
    "green": const(0x00),
    "blue": const(0x10),
    "red": const(0x20),
    "ir": const(0x30),
}

_CHANNELS = (
    ("ir", REG_CS_DATA_IR),
    ("green", REG_CS_DATA_GREEN),
    ("red", REG_CS_DATA_RED),
    ("blue", REG_CS_DATA_BLUE),
)

_GAIN_FACTORS = {
    Gain.X1: 1,
    Gain.X3: 3,
    Gain.X6: 6,
    Gain.X9: 9,
    Gain.X18: 18,
}

_DEFAULT_CCT_MATRIX = (
    (-0.14282, 1.54924, -0.95641),
    (-0.32466, 1.57837, -0.73191),
    (-0.68202, 0.77073, 0.56332),
)

_COLOR_WHEEL_NAMES = (
    "red",
    "orange",
    "yellow",
    "lime",
    "green",
    "spring",
    "cyan",
    "azure",
    "blue",
    "violet",
    "magenta",
    "rose",
)


class LTR381RGB:
    """MicroPython driver for the LTR-381RGB-01 light and color sensor."""

    def __init__(self, i2c, address: int = DEFAULT_I2C_ADDRESS) -> None:
        """Initialize the sensor driver and enable measurements with defaults.

        Parameters:
            i2c (machine.I2C): The bus instance used to communicate with the sensor.
            address (int): The 7-bit I²C address for the device.
        """

        self._i2c = i2c
        self.address = address
        self._register_buffer = bytearray(1)
        self._channel_buffer = bytearray(CHANNEL_REGISTER_SIZE)

        self._detect()
        self.reset()
        self._update_measurement_register(
            resolution_bits=IntegrationTime.MS100,
            rate_bits=MeasurementRate.MS100,
            ensure_rate=False,
        )
        self.gain = Gain.X1
        self.enable()

    def _detect(self) -> None:
        """Read and validate the sensor part and revision identifiers.

        Raises:
            LTR381RGBError: If the detected part identifier does not match the expected value.
        """

        part = self._read_register(REG_PART_ID)
        self._part_id = part >> 4
        self._revision = part & 0x0F
        if self._part_id != EXPECTED_PART_ID:
            raise LTR381RGBError("Unexpected part identifier 0x{:02X}".format(part))

    @property
    def integration_time(self) -> int:
        """Return the raw integration-time bit pattern from the sensor.

        Returns:
            int: The integration time bit-field stored in ``REG_ALS_CS_MEAS_RATE``.
        """

        reg = self._read_register(REG_ALS_CS_MEAS_RATE)
        return reg & MEAS_RESOLUTION_MASK

    @integration_time.setter
    def integration_time(self, value: int) -> None:
        """Configure the integration time using a datasheet-defined bit pattern.

        Parameters:
            value (int): The integration time bit-field to write.

        Raises:
            ValueError: If the bit-field is not supported by the sensor.
        """

        if value not in _INTEGRATION_MS:
            raise ValueError("Unsupported integration time 0x{:02X}".format(value))
        self._update_measurement_register(resolution_bits=value)

    @property
    def integration_time_ms(self) -> int:
        """Return the configured integration time expressed in milliseconds.

        Returns:
            int: The integration time in milliseconds.

        Raises:
            LTR381RGBError: If the stored bit-field cannot be mapped to a known duration.
        """

        bits = self.integration_time
        try:
            return _INTEGRATION_MS[bits]
        except KeyError as exc:
            raise LTR381RGBError("Unknown integration time bits 0x{:02X}".format(bits)) from exc

    @property
    def measurement_rate(self) -> int:
        """Return the raw measurement-rate bit pattern from the sensor.

        Returns:
            int: The measurement rate bit-field stored in ``REG_ALS_CS_MEAS_RATE``.
        """

        reg = self._read_register(REG_ALS_CS_MEAS_RATE)
        return reg & MEAS_RATE_MASK

    @measurement_rate.setter
    def measurement_rate(self, value: int) -> None:
        """Set the measurement cadence, validating against integration timing.

        Parameters:
            value (int): The measurement rate bit-field to write.

        Raises:
            ValueError: If the supplied rate is unsupported or violates the integration constraint.
        """

        if value not in _MEASUREMENT_MS:
            raise ValueError("Unsupported measurement rate 0x{:02X}".format(value))
        current_int = self.integration_time
        if _MEASUREMENT_MS[value] < _INTEGRATION_MS[current_int]:
            raise ValueError("Measurement rate must be >= integration time")
        self._update_measurement_register(rate_bits=value, ensure_rate=False)

    @property
    def measurement_period_ms(self) -> int:
        """Return the actual measurement period in milliseconds.

        Returns:
            int: The configured measurement period in milliseconds.

        Raises:
            LTR381RGBError: If the stored bit-field cannot be mapped to a known duration.
        """

        bits = self.measurement_rate
        try:
            return _MEASUREMENT_MS[bits]
        except KeyError as exc:
            raise LTR381RGBError("Unknown measurement rate bits 0x{:02X}".format(bits)) from exc

    @property
    def gain(self) -> int:
        """Return the configured gain bit pattern.

        Returns:
            int: The gain bit-field stored in ``REG_ALS_CS_GAIN``.
        """

        reg = self._read_register(REG_ALS_CS_GAIN)
        return reg & GAIN_MASK

    @gain.setter
    def gain(self, value: int) -> None:
        """Set the sensor gain using one of the supported bit patterns.

        Parameters:
            value (int): The gain bit-field to write.

        Raises:
            ValueError: If the requested gain is not supported.
        """

        if value not in (Gain.X1, Gain.X3, Gain.X6, Gain.X9, Gain.X18):
            raise ValueError("Unsupported gain 0x{:02X}".format(value))
        self._write_register(REG_ALS_CS_GAIN, value & GAIN_MASK)

    def reset(self) -> None:
        """Issue a software reset and wait for the sensor to reboot.

        """
        try:
            self._write_register(REG_MAIN_CTRL, MAIN_CTRL_SW_RESET)
        except OSError:
            pass  # Some devices NACK during reset
        time.sleep_ms(5)

    def enable(self, *, color_mode: bool = True) -> None:
        """Enable ALS/CS measurements, optionally engaging full color mode.

        Parameters:
            color_mode (bool): Set to ``True`` to enable color sensing. ``False`` enables ALS-only mode.
        """

        value = MAIN_CTRL_ALS_ENABLE
        if color_mode:
            value |= MAIN_CTRL_CS_MODE
        self._write_register(REG_MAIN_CTRL, value)
        time.sleep_ms(5)

    def disable(self) -> None:
        """Disable all ALS/CS measurements.

        """

        self._write_register(REG_MAIN_CTRL, 0x00)

    @property
    def is_data_ready(self) -> bool:
        """Return ``True`` when a new measurement sample is ready to read.

        Returns:
            bool: ``True`` if the data-ready flag is asserted; otherwise ``False``.
        """

        status = self._read_register(REG_MAIN_STATUS)
        return bool(status & MAIN_STATUS_DATA_NEW)

    @property
    def raw_channels(self) -> tuple:
        """Return a fresh (ir, green, red, blue) tuple of raw channel values.

        Returns:
            tuple: A 4-tuple containing the latest IR, green, red, and blue 20-bit samples.
        """

        self._wait_for_sample()
        return self._read_all_channels()

    def _wait_for_sample(self) -> None:
        """Block until a fresh measurement is ready to read."""

        # Add 20% margin + 50ms to account for internal oscillator tolerances
        base_timeout = max(self.measurement_period_ms, self.integration_time_ms)
        timeout = int(base_timeout * 1.2) + 50
        self._poll_ready(timeout)

    @property
    def ambient_light(self) -> int:
        """Return the ALS (green) channel reading as a 20-bit integer.

        Returns:
            int: The raw green-channel count.
        """

        self._wait_for_sample()
        return self._read_channel(REG_CS_DATA_GREEN)

    @classmethod
    def _scale_rgb_tuple(cls, red: int, green: int, blue: int) -> tuple:
        """Convert raw RGB readings into a tuple of 0–255 values.

        The highest raw channel is scaled to 255 and the others are normalized
        proportionally, preserving relative color balance while providing an
        8-bit-friendly tuple for UI usage.
        """

        max_value = max(red, green, blue)
        if max_value <= 0:
            return 0, 0, 0

        def _scale(channel: int) -> int:
            scaled = (channel * RGB_MAX_VALUE + (max_value // 2)) // max_value
            if scaled > RGB_MAX_VALUE:
                return RGB_MAX_VALUE
            if scaled < 0:
                return 0
            return int(scaled)

        return (_scale(red), _scale(green), _scale(blue))

    @property
    def rgb_color(self) -> tuple:
        """Return a per-sample normalized (red, green, blue) tuple scaled to 0–255.

        Returns:
            tuple: A 3-tuple of 8-bit red, green, and blue values where the
                highest channel in the current sample is mapped to 255.
        """

        self._wait_for_sample()
        red, green, blue = self._read_rgb_channels()
        return self._scale_rgb_tuple(red, green, blue)

    @property
    def ambient_rgb_ir(self) -> dict:
        """Return ambient ALS value alongside the normalized RGB tuple and IR count.

        Returns:
            dict: Keys include ``ambient`` (raw green count), ``rgb`` (per-sample
                normalized 0–255 tuple), and ``ir`` (raw infrared count).
        """

        ir, green, red, blue = self.raw_channels
        rgb_scaled = self._scale_rgb_tuple(red, green, blue)
        return {
            "ambient": green,
            "rgb": rgb_scaled,
            "ir": ir,
        }

    @property
    def ir_light(self) -> int:
        """Return the IR-only channel for API compatibility with LTR-329.

        Returns:
            int: The raw infrared channel count.
        """

        self._wait_for_sample()
        return self._read_channel(REG_CS_DATA_IR)

    @property
    def approximate_color(self) -> str:
        """Return a rough color name derived from the RGB channels.

        Returns:
            str: A hue name selected from ``_COLOR_WHEEL_NAMES``.
        """

        self._wait_for_sample()
        red, green, blue = self._read_rgb_channels()

        # Convert to floats to reuse the hue and saturation logic typically
        # expressed for normalized RGB values while still operating on raw
        # counts. Using floats avoids repeated integer conversions later.
        r = float(red)
        g = float(green)
        b = float(blue)

        max_val = max(r, g, b)
        min_val = min(r, g, b)

        # All channels zero means complete darkness; fall back to the first
        # entry in the color wheel to avoid dividing by zero.
        if max_val <= 0.0:
            return _COLOR_WHEEL_NAMES[0]

        diff = max_val - min_val
        if diff == 0.0:
            return _COLOR_WHEEL_NAMES[0]

        # Very low saturation is effectively grey/white, so classify it as the
        # neutral "red" bucket as a conservative default.
        saturation = diff / max_val
        if saturation < 0.05:
            return _COLOR_WHEEL_NAMES[0]

        # Compute the hue angle in the standard [0, 360) range using the
        # dominant channel as the reference sector on the color wheel.
        if max_val == r:
            hue_section = (g - b) / diff % 6.0
        elif max_val == g:
            hue_section = ((b - r) / diff) + 2.0
        else:
            hue_section = ((r - g) / diff) + 4.0

        hue_deg = (hue_section * 60.0) % 360.0
        # Quantize the hue into 12 evenly spaced slices (30° each) to pick a
        # descriptive color name from the pre-defined wheel.
        index = int((hue_deg + 15.0) // 30.0) % len(_COLOR_WHEEL_NAMES)
        return _COLOR_WHEEL_NAMES[index]

    def lux_from_raw(
        self,
        green,
        ir,
        *,
        gain_bits=None,
        integration_bits=None,
        window_factor=1.0,
        c1=0.033,
        alpha=0.8,
    ):
        """Convert raw green/IR counts to Lux using datasheet coefficients.

        Parameters:
            green (int | float): The raw ambient (green) channel reading.
            ir (int | float): The raw infrared channel reading.
            gain_bits (int, optional): The gain bit-field to use; defaults to the current device setting.
            integration_bits (int, optional): The integration-time bit-field; defaults to the current device setting.
            window_factor (float): Optical attenuation factor of any cover window.
            c1 (float): Coefficient used to compensate IR influence on the ALS channel.
            alpha (float): Scaling factor from datasheet equation 15.

        Returns:
            float: The computed lux value (non-negative).

        Raises:
            LTR381RGBError: If gain or integration parameters are invalid.
        """

        if gain_bits is None:
            gain_bits = self.gain
        if integration_bits is None:
            integration_bits = self.integration_time

        gain_factor = _GAIN_FACTORS.get(gain_bits)
        if not gain_factor:
            raise LTR381RGBError("Unsupported gain setting 0x{:02X}".format(gain_bits))

        integration_ms = _INTEGRATION_MS.get(integration_bits)
        if integration_ms is None:
            raise LTR381RGBError("Unsupported integration time bits 0x{:02X}".format(integration_bits))

        integration_factor = integration_ms / 100.0
        if integration_factor <= 0:
            raise LTR381RGBError("Integration factor must be positive")

        corrected = float(green) - (c1 * float(ir))
        if corrected < 0:
            corrected = 0.0

        denominator = gain_factor * integration_factor
        if denominator <= 0:
            raise LTR381RGBError("Gain and integration combination must be positive")

        if window_factor <= 0:
            raise LTR381RGBError("Window factor must be positive")

        lux = alpha * corrected / (denominator * window_factor)
        return max(lux, 0.0)

    @property
    def lux(self) -> float:
        """Return the estimated lux value from a fresh measurement.

        Returns:
            float: The computed illuminance in lux.
        """

        self._wait_for_sample()
        green = self._read_channel(REG_CS_DATA_GREEN)
        ir = self._read_channel(REG_CS_DATA_IR)
        return self.lux_from_raw(
            green,
            ir,
            gain_bits=self.gain,
            integration_bits=self.integration_time,
        )

    def color_temperature_from_raw(
        self,
        red,
        green,
        blue,
        *,
        matrix=None,
    ):
        """Estimate correlated color temperature (Kelvin) from raw RGB counts.

        Parameters:
            red (int | float): The raw red channel reading.
            green (int | float): The raw green channel reading.
            blue (int | float): The raw blue channel reading.
            matrix (tuple, optional): A 3x3 conversion matrix mapping RGB to XYZ.

        Returns:
            float: The correlated color temperature in kelvin.

        Raises:
            LTR381RGBError: If the RGB sample cannot produce a valid CCT.
        """

        if matrix is None:
            matrix = _DEFAULT_CCT_MATRIX

        (m11, m12, m13), (m21, m22, m23), (m31, m32, m33) = matrix

        # Map the sensor's raw RGB counts into the CIE XYZ color space using the
        # provided 3×3 transformation matrix. Each axis is a weighted sum of the
        # original channel magnitudes.
        X = (m11 * red) + (m12 * green) + (m13 * blue)
        Y = (m21 * red) + (m22 * green) + (m23 * blue)
        Z = (m31 * red) + (m32 * green) + (m33 * blue)

        # Normalize the XYZ tristimulus values into the chromaticity coordinates
        # (x, y). If the total energy is zero, the sample cannot be classified.
        denom = X + Y + Z
        if denom <= 0:
            raise LTR381RGBError("Invalid RGB sample for color temperature calculation")

        x = X / denom
        y = Y / denom

        # McCamy's approximation operates on the slope between the chromaticity
        # point and a reference white (x≈0.3320, y≈0.1858). If the denominator is
        # zero the temperature would be undefined for this sample.
        denom_n = 0.1858 - y
        if denom_n == 0:
            raise LTR381RGBError("Color temperature undefined for y=0.1858")

        n = (x - 0.3320) / denom_n
        # Evaluate McCamy's cubic polynomial to convert the slope into an
        # estimated correlated color temperature in Kelvin.
        cct = (449.0 * n * n * n) + (3525.0 * n * n) + (6823.3 * n) + 5520.33
        return max(cct, 0.0)

    @property
    def color_temperature(self) -> float:
        """Return the estimated color temperature (Kelvin) using the default matrix.

        Returns:
            float: The correlated color temperature derived from a fresh sample.
        """

        self._wait_for_sample()
        red, green, blue = self._read_rgb_channels()
        return self.color_temperature_from_raw(red, green, blue)

    def set_thresholds(self, low: int, high: int) -> None:
        """Configure low and high ALS thresholds for interrupt generation.

        Parameters:
            low (int): The lower threshold (0–0xFFFFF).
            high (int): The upper threshold (0–0xFFFFF).

        Raises:
            ValueError: If the thresholds are out of range or inverted.
        """

        if not 0 <= low <= DATA_20BIT_MASK:
            raise ValueError("Low threshold must be between 0 and 0xFFFFF")
        if not 0 <= high <= DATA_20BIT_MASK:
            raise ValueError("High threshold must be between 0 and 0xFFFFF")
        if low > high:
            raise ValueError("Low threshold must be <= high threshold")
        self._write_threshold(REG_ALS_THRESH_LOW_L, low)
        self._write_threshold(REG_ALS_THRESH_UP_L, high)

    def get_thresholds(self) -> tuple:
        """Return the currently configured (low, high) ALS thresholds.

        Returns:
            tuple: A ``(low, high)`` tuple of 20-bit threshold values.
        """

        low = self._read_threshold(REG_ALS_THRESH_LOW_L)
        high = self._read_threshold(REG_ALS_THRESH_UP_L)
        return low, high

    def configure_interrupts(self, enable: bool, persist: int = 0, source: str = "green") -> None:
        """Enable or disable threshold interrupts with persistence and channel selection.

        Parameters:
            enable (bool): ``True`` to enable the interrupt output, ``False`` to disable it.
            persist (int): Number of consecutive threshold events required before triggering (0–15).
            source (str): Channel to monitor (``"green"``, ``"red"``, ``"blue"``, or ``"ir"``).

        Raises:
            ValueError: If ``persist`` or ``source`` is outside the supported range.
        """

        if persist < 0 or persist > 15:
            raise ValueError("Persist must be between 0 and 15")
        try:
            source_bits = _INT_SOURCE_BITS[source]
        except KeyError as exc:
            raise ValueError("Unsupported interrupt source '{}'".format(source)) from exc

        cfg = self._read_register(REG_INT_CFG)
        cfg &= ~(INT_CFG_SOURCE_MASK | INT_CFG_ENABLE)
        cfg |= source_bits
        if enable:
            cfg |= INT_CFG_ENABLE
        self._write_register(REG_INT_CFG, cfg)

        if enable:
            self._write_register(REG_INT_PST, (persist << 4) & INT_PST_PERSIST_MASK)
        else:
            self._write_register(REG_INT_PST, 0x00)

    @property
    def part_revision(self) -> tuple:
        """Return the (part_id, revision) tuple detected at initialization.

        Returns:
            tuple: A ``(part_id, revision)`` pair identifying the sensor.
        """

        return self._part_id, self._revision

    def reboot(self, timeout_ms: int = 100) -> None:
        """Reset and re-enable the sensor, waiting until data is ready again.

        Parameters:
            timeout_ms (int): Maximum time in milliseconds to wait for fresh data.

        Raises:
            LTR381RGBTimeout: If the sensor does not report ready before the timeout elapses.
        """

        self.reset()
        self.enable()
        self._poll_ready(timeout_ms)

    def _poll_ready(self, timeout_ms: int = 100) -> None:
        """Block until the data-ready flag is set or the timeout expires.

        Parameters:
            timeout_ms (int): Maximum number of milliseconds to wait.

        Raises:
            LTR381RGBTimeout: If the timeout elapses before data becomes ready.
        """

        deadline = ticks_add(ticks_ms(), timeout_ms)
        while True:
            if self.is_data_ready:
                return
            if ticks_diff(ticks_ms(), deadline) >= 0:
                raise LTR381RGBTimeout("Sensor data not ready")
            time.sleep_ms(5)

    def _update_measurement_register(self, resolution_bits=None, rate_bits=None, ensure_rate: bool = True) -> None:
        """Update measurement timing register while enforcing datasheet constraints.

        Parameters:
            resolution_bits (int | None): Optional integration-time bit-field override.
            rate_bits (int | None): Optional measurement-rate bit-field override.
            ensure_rate (bool): When ``True``, adjust the rate to satisfy integration constraints.
        """

        reg = self._read_register(REG_ALS_CS_MEAS_RATE)
        if resolution_bits is not None:
            reg = (reg & ~MEAS_RESOLUTION_MASK) | (resolution_bits & MEAS_RESOLUTION_MASK)
        if rate_bits is not None:
            reg = (reg & ~MEAS_RATE_MASK) | (rate_bits & MEAS_RATE_MASK)

        if ensure_rate:
            rate_bits = reg & MEAS_RATE_MASK
            resolution_bits = reg & MEAS_RESOLUTION_MASK
            if (
                resolution_bits in _INTEGRATION_MS
                and rate_bits in _MEASUREMENT_MS
                and _MEASUREMENT_MS[rate_bits] < _INTEGRATION_MS[resolution_bits]
            ):
                reg = (reg & ~MEAS_RATE_MASK) | self._select_rate(_INTEGRATION_MS[resolution_bits])

        self._write_register(REG_ALS_CS_MEAS_RATE, reg)

    def _select_rate(self, minimum_ms: int) -> int:
        """Return the slowest supported measurement rate not less than ``minimum_ms``.

        Parameters:
            minimum_ms (int): Minimum acceptable measurement interval in milliseconds.

        Returns:
            int: The chosen measurement rate bit-field.
        """

        for bits, ms in _MEASUREMENT_OPTIONS:
            if ms >= minimum_ms:
                return bits
        return MeasurementRate.MS2000

    def _read_all_channels(self) -> tuple:
        """Read all color sensor channels in (ir, green, red, blue) order.

        Returns:
            tuple: A 4-tuple of 20-bit readings for IR, green, red, and blue channels.
        """

        return tuple(self._read_channel(base) for _, base in _CHANNELS)

    def _read_rgb_channels(self) -> tuple:
        """Read the red, green, and blue color channels in order.

        Returns:
            tuple: A 3-tuple of 20-bit readings for red, green, and blue channels.
        """

        red = self._read_channel(REG_CS_DATA_RED)
        green = self._read_channel(REG_CS_DATA_GREEN)
        blue = self._read_channel(REG_CS_DATA_BLUE)
        return red, green, blue

    def _read_channel(self, base_register: int) -> int:
        """Read a single 20-bit channel value starting at the given register.

        Parameters:
            base_register (int): Register address of the channel's least significant byte.

        Returns:
            int: The 20-bit channel reading.
        """

        self._i2c.readfrom_mem_into(self.address, base_register, self._channel_buffer)
        return (
            ((self._channel_buffer[2] & DATA_HIGH_NIBBLE_MASK) << 16)
            | (self._channel_buffer[1] << 8)
            | self._channel_buffer[0]
        )

    def _write_threshold(self, base_register: int, value: int) -> None:
        """Write a 20-bit threshold value to the specified register pair.

        Parameters:
            base_register (int): Register address of the least significant byte.
            value (int): 20-bit threshold value to store.
        """

        self._channel_buffer[0] = value & 0xFF
        self._channel_buffer[1] = (value >> 8) & 0xFF
        self._channel_buffer[2] = (value >> 16) & DATA_HIGH_NIBBLE_MASK
        self._i2c.writeto_mem(self.address, base_register, self._channel_buffer)

    def _read_threshold(self, base_register: int) -> int:
        """Read a 20-bit threshold value from the specified register pair.

        Parameters:
            base_register (int): Register address of the least significant byte.

        Returns:
            int: The 20-bit threshold value.
        """

        self._i2c.readfrom_mem_into(self.address, base_register, self._channel_buffer)
        return (
            ((self._channel_buffer[2] & DATA_HIGH_NIBBLE_MASK) << 16)
            | (self._channel_buffer[1] << 8)
            | self._channel_buffer[0]
        )

    def _write_register(self, register: int, value: int) -> None:
        """Write a single byte to the provided register address.

        Parameters:
            register (int): Register address to write.
            value (int): Byte value to store.
        """

        self._register_buffer[0] = value & 0xFF
        self._i2c.writeto_mem(self.address, register, self._register_buffer)

    def _write_registers(self, start_register: int, values) -> None:
        """Write a sequence of bytes starting at ``start_register``.

        Parameters:
            start_register (int): Address of the first register to write.
            values (Iterable[int] | bytes | bytearray): Sequence of byte values to store.
        """

        if not isinstance(values, (bytes, bytearray)):
            values = bytes(values)
        self._i2c.writeto_mem(self.address, start_register, values)

    def _read_register(self, register: int) -> int:
        """Read and return a single byte from the provided register.

        Parameters:
            register (int): Register address to read.

        Returns:
            int: The byte value read from the register.
        """

        self._i2c.readfrom_mem_into(self.address, register, self._register_buffer)
        return self._register_buffer[0]

    def _read_registers(self, start_register: int, length: int) -> bytes:
        """Read multiple bytes starting at ``start_register``.

        Parameters:
            start_register (int): Address of the first register to read.
            length (int): Number of bytes to read.

        Returns:
            bytes: The bytes read from the device.
        """

        buf = bytearray(length)
        self._i2c.readfrom_mem_into(self.address, start_register, buf)
        return bytes(buf)

    def _read_word(self, register_low: int, register_high: int) -> int:
        """Read a 16-bit little-endian word composed of low/high registers.

        Parameters:
            register_low (int): Register holding the least significant byte.
            register_high (int): Register holding the most significant byte.

        Returns:
            int: The combined 16-bit value.
        """

        low = self._read_register(register_low)
        high = self._read_register(register_high)
        return (high << 8) | low
