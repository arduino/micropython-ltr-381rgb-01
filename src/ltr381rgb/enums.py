"""Enumerations describing supported configuration options for the LTR-381RGB-01."""

try:  # pragma: no cover - CPython fallback for linting
    from micropython import const  # type: ignore
except ImportError:  # pragma: no cover - used outside MicroPython
    def const(value):  # type: ignore
        return value


_INT_MS400 = const(0x00)
_INT_MS200 = const(0x10)
_INT_MS100 = const(0x20)
_INT_MS50 = const(0x30)
_INT_MS25 = const(0x40)

_RATE_MS25 = const(0x00)
_RATE_MS50 = const(0x01)
_RATE_MS100 = const(0x02)
_RATE_MS200 = const(0x03)
_RATE_MS500 = const(0x04)
_RATE_MS1000 = const(0x05)
_RATE_MS2000 = const(0x06)

_GAIN_X1 = const(0x00)
_GAIN_X3 = const(0x01)
_GAIN_X6 = const(0x02)
_GAIN_X9 = const(0x03)
_GAIN_X18 = const(0x04)


class IntegrationTime:
    """Integration timing options encoded in ``ALS_CS_MEAS_RATE`` bits 6:4."""

    MS400 = _INT_MS400  # 20-bit resolution, 400 ms
    MS200 = _INT_MS200  # 19-bit resolution, 200 ms
    MS100 = _INT_MS100  # 18-bit resolution, 100 ms (default)
    MS50 = _INT_MS50    # 17-bit resolution, 50 ms
    MS25 = _INT_MS25    # 16-bit resolution, 25 ms


class MeasurementRate:
    """Measurement repeat intervals encoded in ``ALS_CS_MEAS_RATE`` bits 2:0."""

    MS25 = _RATE_MS25
    MS50 = _RATE_MS50
    MS100 = _RATE_MS100
    MS200 = _RATE_MS200
    MS500 = _RATE_MS500
    MS1000 = _RATE_MS1000
    MS2000 = _RATE_MS2000


class Gain:
    """Selectable analog gain factors encoded in ``ALS_CS_GAIN`` bits 2:0."""

    X1 = _GAIN_X1
    X3 = _GAIN_X3
    X6 = _GAIN_X6
    X9 = _GAIN_X9
    X18 = _GAIN_X18
