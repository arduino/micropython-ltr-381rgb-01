# 📦 MicroPython LTR-381RGB-01 Driver

This package provides a MicroPython driver for Lite-On's LTR-381RGB-01 ambient light and color sensor.

## ✨ Features

- **Raw channel reads**: 20-bit readings for IR, green (ALS), red, and blue photodiodes.
- **Lux & color temperature**: Datasheet-based lux formula and McCamy's CCT approximation, with optional calibration parameters.
- **Flexible configuration**: Programmable integration time, measurement rate, and gain with automatic constraint enforcement.
- **Interrupts**: Threshold-based interrupt with per-channel source selection and configurable persistence.
- **Color helpers**: Per-sample RGB tuple normalized to 0–255, plus a coarse hue-name classifier.
- **Easy I2C integration**: Standard MicroPython `machine.I2C` compatibility — works on any board with I2C support.

## ✅ Supported Boards

Any board that can run a modern version of MicroPython and exposes an I2C interface. Specify the bus at construction time, e.g. `sensor = LTR381RGB(I2C(0))`.

## ⚙️ Installation

The easiest way is to use the [Arduino MicroPython Package Installer](https://github.com/arduino/lab-micropython-package-installer/releases/latest). Otherwise you can use [mpremote and mip](https://docs.micropython.org/en/latest/reference/packages.html#packages): 

```bash
mpremote mip install github:arduino/micropython-LTR-381RGB-01
```

## 🧑‍💻 Developer Installation

Clone the repository and run examples directly with `mpremote` by mounting the `src` directory on the board:

```bash
mpremote mount src run examples/minimal.py
```

If your board is not detected automatically, specify the port explicitly:

```bash
mpremote connect /dev/ttyACM0 mount src run examples/minimal.py
```

## 🏃 Quick Start

```python
import time
from machine import I2C
from ltr381rgb.device import LTR381RGB

i2c = I2C(0)
sensor = LTR381RGB(i2c)

while True:
    if not sensor.data_ready:
        time.sleep_ms(5)
        continue

    data = sensor.ambient_rgb_ir
    print("Ambient light:", data["ambient"])
    print("RGB (R, G, B):", data["rgb"])
    print("Infrared:     ", data["ir"])
```

See the [examples](examples/) for gain/timing configuration, lux, color temperature, interrupts, and more.

## 📖 Documentation

- `src/ltr381rgb/constants.py` – Register addresses and bit masks.
- `src/ltr381rgb/enums.py` – Enumerations for integration time, measurement rate, and gain.
- `src/ltr381rgb/device.py` – The `LTR381RGB` driver implementation.
- `src/ltr381rgb/errors.py` – Exception hierarchy shared across the package.

Refer to the [LTR-381RGB-01 datasheet](https://optoelectronics.liteon.com/upload/download/DS86-2018-0007/LTR-381RGB-01_Final_DS_V1.8.PDF) for register descriptions, electrical characteristics, and timing constraints.

## 🐛 Reporting Issues

If you encounter any issue, please open a bug report [here](https://github.com/arduino/micropython-LTR-381RGB-01/issues).

## 💪 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
