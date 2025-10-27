"""Register definitions and bit masks for the LTR-381RGB-01 sensor."""

from micropython import const


DEFAULT_I2C_ADDRESS = const(0x53)

# Core register map
REG_MAIN_CTRL = const(0x00)
REG_ALS_CS_MEAS_RATE = const(0x04)
REG_ALS_CS_GAIN = const(0x05)
REG_PART_ID = const(0x06)
REG_MAIN_STATUS = const(0x07)

REG_CS_DATA_IR = const(0x0A)
REG_CS_DATA_GREEN = const(0x0D)
REG_CS_DATA_RED = const(0x10)
REG_CS_DATA_BLUE = const(0x13)

REG_INT_CFG = const(0x19)
REG_INT_PST = const(0x1A)

REG_ALS_THRESH_UP_L = const(0x21)
REG_ALS_THRESH_UP_M = const(0x22)
REG_ALS_THRESH_UP_H = const(0x23)
REG_ALS_THRESH_LOW_L = const(0x24)
REG_ALS_THRESH_LOW_M = const(0x25)
REG_ALS_THRESH_LOW_H = const(0x26)

# MAIN_CTRL bit positions
MAIN_CTRL_SW_RESET = const(0x10)
MAIN_CTRL_CS_MODE = const(0x04)
MAIN_CTRL_ALS_ENABLE = const(0x02)

# MAIN_STATUS bits
MAIN_STATUS_POWER_ON = const(0x20)
MAIN_STATUS_INT = const(0x10)
MAIN_STATUS_DATA_NEW = const(0x08)

# ALS/CS measurement register masks
MEAS_RESOLUTION_MASK = const(0x70)
MEAS_RATE_MASK = const(0x07)

# Gain mask
GAIN_MASK = const(0x07)

# Interrupt configuration masks
INT_CFG_SOURCE_MASK = const(0x30)
INT_CFG_ENABLE = const(0x04)

# Interrupt persistence mask
INT_PST_PERSIST_MASK = const(0xF0)

# Data register helper constants
CHANNEL_REGISTER_SIZE = const(3)
DATA_HIGH_NIBBLE_MASK = const(0x0F)
DATA_20BIT_MASK = const(0x0FFFFF)
