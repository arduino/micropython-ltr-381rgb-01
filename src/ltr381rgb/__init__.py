"""MicroPython driver for the LTR-381RGB-01 light and color sensor.

The package exposes a fully functional device class that handles register
configuration, data acquisition, and interrupt management using an
``machine.I2C``-compatible bus. Utility enums help express integration time,
measurement cadence, and gain settings in a human-friendly way while keeping
the underlying bit-fields aligned with the datasheet.
"""

from .device import LTR381RGB
from .enums import Gain, IntegrationTime, MeasurementRate
from .errors import LTR381RGBError, LTR381RGBTimeout

__all__ = [
    "LTR381RGB",
    "Gain",
    "IntegrationTime",
    "MeasurementRate",
    "LTR381RGBError",
    "LTR381RGBTimeout",
]
