"""Exception hierarchy for the LTR-381RGB-01 driver."""


class LTR381RGBError(Exception):
    """Base exception for driver level failures."""


class LTR381RGBTimeout(LTR381RGBError):
    """Raised when sensor data fails to become ready within the expected window."""
