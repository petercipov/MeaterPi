# MeaterPi

Target hardware: Raspberry Pi Zero 2 W

Hardware:
- Raspberry Pi Zero 2 W
- M5Stack ENV III Unit

## Overview

This project is a Raspberry Pi Python package for reading temperature and humidity from the M5Stack ENV III Unit (SHT30 sensor) via I2C. The application prints environmental data to standard output every 5 seconds.

## Wiring

Connect the ENV III unit to the Raspberry Pi Zero 2 W I2C pins:

- SDA -> GPIO2 (physical pin 3)
- SCL -> GPIO3 (physical pin 5)
- 5V -> 5V (physical pin 2 or 4)
- GND -> GND (physical pin 6)

> The ENV III uses the Pi's 5V supply for power. The I2C lines remain SDA/SCL on GPIO2 and GPIO3.

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

3. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

4. Verify the I2C bus is available:

```bash
sudo i2cdetect -y 1
```

## Run

Activate the virtual environment and run:

```bash
source venv/bin/activate
python3 -m meaterpi
```

The program prints detected I2C addresses and environment values to stdout every 5 seconds.

## Notes

- Uses direct `smbus2` drivers for both sensors:
  - **SHT30** at I2C address 0x44 (temperature & humidity)
  - **QMP6988** at I2C address 0x70 (barometric pressure)
- Prints temperature (°C), humidity (%), and pressure (hPa)
- Sensor readings are taken every 5 seconds
