# MeaterPi

Target hardware: Raspberry Pi Zero 2 W

Hardware:
- Raspberry Pi Zero 2 W
- M5Stack ENV III Unit
- ARCTIC P12 Pro PST Fan (12V, 4-pin PWM)

## Overview

This project is a Raspberry Pi Python package for reading temperature and humidity from the M5Stack ENV III Unit (SHT30 sensor) via I2C. The application prints environmental data to standard output every 5 seconds.

## Wiring

> Note: The Raspberry Pi Zero 2 W uses a 40-pin GPIO header for all connections.

### Power Architecture

- **12V PSU** powers both Raspberry Pi (via step-down converter) and fan
- Step-down converter (LM7805 or buck converter module) provides regulated 5V to Raspi 5V GPIO header
- All GND connections tied together

### ENV III Unit (I2C Temperature, Humidity, Pressure)

Connect the ENV III unit to the Raspberry Pi Zero 2 W I2C pins:

- SDA -> GPIO2 (physical pin 3)
- SCL -> GPIO3 (physical pin 5)
- 5V -> 5V (physical pin 2 or 4)
- GND -> GND (physical pin 6)

> The ENV III uses the Pi's 5V supply for power. The I2C lines remain SDA/SCL on GPIO2 and GPIO3.
> Note: The ENV III unit uses a `HY2.0-4P` connector.

### ARCTIC P12 Pro PST Fan (12V PWM + RPM Tachometer)

**Fan connector pinout (4-pin):**
- Pin 1 (Black) → GND
- Pin 2 (Yellow) → 12V
- Pin 3 (Green) → RPM feedback / tachometer
- Pin 4 (Blue) → PWM control

> Note: The ARCTIC P12 Pro PST fan uses a 4-pin Molex connector.
> The pinout above follows the standard 4-pin PC PWM fan convention. Check connector orientation before wiring.

**Wiring:**

| Fan Pin | Connection |
|---------|-----------|
| GND (black) | Raspi GND (GPIO pin 6, 9, 14, 20, 25, etc.) |
| 12V (yellow) | 12V PSU output |
| RPM / tach (green) | Voltage divider (see below) → GPIO27 (physical pin 13) |
| PWM (blue) | GPIO17 (physical pin 11) |

**Voltage Divider for RPM feedback** (5V fan signal → 3.3V Raspi GPIO):
- Fan RPM / tach (green) → 1kΩ resistor → GPIO27
- GPIO27 → 2kΩ resistor → GND

This divides 5V to 3.3V, safe for Raspi GPIO.

**2N3904 PWM transistor:**
- Datasheet: [onsemi 2N3904](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf)
- Verified marking: `2N3904 H331`
- Pinout, flat face toward you and legs downward:

| Pin | Function |
|-----|----------|
| 1 | Emitter |
| 2 | Base |
| 3 | Collector |

This matches the diode-test check where red on pin 2 reads about 0.66 V to pin 1 and about 0.65 V to pin 3.

**Power connections:**
- 12V PSU GND → Raspi GND (common ground)
- 12V PSU +12V → Fan 12V pin
- 12V PSU +12V → Step-down converter input
- Step-down converter +5V output → Raspi 5V GPIO header pin (physical pin 4 or 2)
- Step-down converter GND → Raspi GND (GPIO pin 6 or 9)

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

## Fan PWM Test

With the breadboard Q1 driver connected to GPIO17, run a slow PWM sweep:

```bash
sudo apt install -y python3-lgpio
/usr/bin/python3 scripts/fan_pwm_sweep.py
```

The script uses BCM GPIO17 at 20 kHz and repeatedly sweeps the fan request between 95% and 10%, then requests 0% for 5 seconds. Each normal sweep step also holds for 5 seconds. Stop it with `Ctrl-C`; cleanup releases Q1 so the fan returns to full speed. The PC fan PWM target is normally 25 kHz, but `lgpio` rejected 25 kHz on this Raspberry Pi setup with `bad PWM frequency`.

## Notes

- Uses direct `smbus2` drivers for both sensors:
  - **SHT30** at I2C address 0x44 (temperature & humidity with CRC validation)
  - **QMP6988** at I2C address 0x70 (barometric pressure with M5Stack fixed-point conversion algorithm)
- Implements M5Stack's official QMP6988 fixed-point calibration and conversion formula for accurate pressure readings
- PWM fan control via GPIO17 (12V ARCTIC P12 Pro PST)
- RPM feedback from fan via GPIO27 with voltage divider (5V → 3.3V)
- Prints temperature (°C), humidity (%), and pressure (hPa)
- Sensor readings and fan status are taken every 5 seconds
- Requires:
  - 12V regulated power supply (capable of powering Raspi via buck converter + fan)
  - 5V step-down converter (LM7805 or buck converter module) for Raspi
  - 1kΩ and 2kΩ resistors for RPM voltage divider
