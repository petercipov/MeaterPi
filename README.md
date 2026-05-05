# MeaterPi

Target hardware: Raspberry Pi Zero 2 W

Hardware:
- Raspberry Pi Zero 2 W
- M5Stack ENV III Unit

## Overview

This project is a Raspberry Pi Python package for connecting an M5Stack ENV III environmental sensor unit using the Pi's I2C pins. For now, the application prints environment values to standard output.

## Wiring

Connect the ENV III unit to the Raspberry Pi Zero 2 W I2C pins:

- SDA -> GPIO2 (physical pin 3)
- SCL -> GPIO3 (physical pin 5)
- 3.3V -> 3.3V (physical pin 1)
- GND -> GND (physical pin 6)

> Use the Pi's 3.3V supply only. The M5Stack ENV III is a 3.3V I2C device, so do not connect it to 5V.

## Setup

0. Clone the repository on your Raspberry Pi using HTTPS:

```bash
sudo apt update
sudo apt install -y git
cd ~
git clone https://github.com/petercipov/MeaterPi.git
cd MeaterPi
```

1. Enable Interface Options > I2C on the Raspberry Pi with `raspi-config`.
2. Install required system packages for Raspberry Pi OS Trixie:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-smbus i2c-tools
```

3. Install Python dependencies and the project package:

```bash
python3 -m pip install --user -r requirements.txt
python3 -m pip install --user -e .
```

4. Verify the I2C bus is available:

```bash
sudo i2cdetect -y 1
```

## Run

```bash
python3 -m meaterpi
```

The program prints detected I2C addresses and environment values to stdout every 5 seconds.

## Notes

- `src/meaterpi/env3.py` currently returns placeholder environmental data.
- Replace the placeholder logic with real I2C sensor reads once the ENV III hardware is available.
