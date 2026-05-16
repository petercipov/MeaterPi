# MeaterPi PCB

KiCad starter project for a Raspberry Pi Zero 2 W carrier board.

## Design Intent

- External XY3606 step-down module handles power conversion.
- The XY3606 module receives the 12 V supply directly.
- This carrier receives:
  - +12 V for the fan rail
  - +5 V for the Raspberry Pi and ENV III rail
  - shared GND
- 40-pin Raspberry Pi GPIO header
- M5Stack ENV III HY2.0/Grove-style 4-pin connector
- 4-pin PC PWM fan connector
- Open-drain fan PWM driver from GPIO17
- Fan tach/RPM path to GPIO27

## Power Architecture

The carrier board uses power option A:

1. Plug the 12 V adapter into the external XY3606 module.
2. Wire the XY3606/module input-side 12 V and GND to this carrier.
3. Wire the XY3606 5 V output and GND to this carrier.
4. The carrier distributes +12 V only to the fan header and +5 V to the Raspberry Pi/ENV III rail.

Removed from this carrier design:

- On-board 12 V barrel jack
- Input polyfuse
- PMOS reverse-polarity protection
- TVS diode
- Bulk 12 V input capacitor
- 12 V bypass capacitor
- On-board/generic buck converter footprint

## Reference Designator Shortcuts

These are the short labels printed on the schematic/PCB:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `C` | Capacitor | `C3` 5 V bypass capacitor |
| `J` | Connector/header/jack | `J1` external power connector |
| `Q` | Transistor | `Q1` PWM NPN transistor |
| `R` | Resistor | `R2` PWM base resistor |

## Component Reference

| Ref | Value / Part | Purpose |
|-----|--------------|---------|
| `J1` | `POWER_FROM_XY3606` | 4-pin screw terminal from the external XY3606/power wiring: +12 V, GND, +5 V, GND. |
| `J2` | `RASPBERRY_PI_GPIO` | 40-pin Raspberry Pi GPIO socket/header connection. |
| `J3` | `ENV_III` | 4-pin HY2.0/Grove-style connector for the M5Stack ENV III sensor. |
| `J4` | `4PIN_PWM_FAN` | Standard 4-pin PC PWM fan connector. |
| `Q1` | `2N3904` | NPN transistor used as the open-collector PWM pull-down driver for fan pin 4. |
| `R2` | 4.7k | Base resistor between Raspberry Pi GPIO17 and Q1 base. |
| `R3` | 100k | Pull-down resistor for Q1 base, keeping fan PWM released during boot/reset. |
| `R4` | 10k | 3.3 V pull-up for the fan tach output. Populate for the standard PC fan open-drain/open-collector tach signal. |
| `R5` | 1k | Series resistor between fan tach and Raspberry Pi GPIO27. Populate for the default tach circuit. |
| `C3` | 100 nF | 5 V rail bypass capacitor near the Raspberry Pi/ENV III rail. |

Q1 datasheet: [onsemi 2N3904](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf)

## Important Pin Assumptions

### Q1 2N3904 Transistor

Verified for the `2N3904 H331` TO-92 part by diode test:

| Pin | Function |
|-----|----------|
| 1 | Emitter |
| 2 | Base |
| 3 | Collector |

With the flat face toward you and the legs downward, the pinout is `E-B-C` from left to right.

### Power Connector

J1 receives power from the external XY3606 module and 12 V input wiring:

| Pin | Signal |
|-----|--------|
| 1 | +12V_EXT |
| 2 | GND |
| 3 | +5V |
| 4 | GND |

The XY3606 module has common input/output ground, so both J1 GND pins should connect to the same shared ground system.

### Fan Header

Standard 4-pin PC PWM fan convention:

| Pin | Signal |
|-----|--------|
| 1 | GND |
| 2 | +12V |
| 3 | Tach / RPM sense |
| 4 | PWM control |

### Fan Tach Circuit

Use the standard PC fan tach assumption as the default:

| Ref | Populate | Purpose |
|-----|----------|---------|
| `R4` | 10k | Pulls the open-drain/open-collector fan tach output up to 3.3 V. |
| `R5` | 1k | Series protection/current limiting between tach and GPIO27. |

This keeps GPIO27 Pi-safe because the tach high level is 3.3 V. A typical PC fan tach output pulls the line low twice per revolution and otherwise leaves it floating, so the board must provide the pull-up.

### ENV III Connector

M5Stack ENV III PORT.A convention:

| Pin | Wire | Signal |
|-----|------|--------|
| 1 | Black | GND |
| 2 | Red | 5V |
| 3 | Yellow | ENV3_SDA |
| 4 | White | ENV3_SCL |

## Breadboard Test

Use the breadboard power rails as:

| Rail | Signal |
|------|--------|
| Blue / `-` | GND |
| Red / `+` | +5 V or +12 V, depending on the circuit being tested |

The rail color is only a convention. Verify with a multimeter, and check whether the breadboard power rails are split in the middle.

### Q1 Fan PWM Driver

Test Q1 with the same pinout used by the schematic and PCB:

| 2N3904 Pin | Function | Breadboard Connection |
|------------|----------|-----------------------|
| 1 | Emitter | GND / blue rail |
| 2 | Base | R2 and R3 base node |
| 3 | Collector | Fan PWM control wire / fan pin 4 |

With the flat face toward you and the legs downward, the Q1 pins are `E-B-C` from left to right.

Use these through-hole resistors for the breadboard test:

| Ref | Breadboard Part | Connection |
|-----|-----------------|------------|
| `R2` | 4.7k, 1/4 W, 5% | Raspberry Pi GPIO17 to Q1 base / pin 2 |
| `R3` | 100k, 1/4 W, 5% | Q1 base / pin 2 to GND |

Q1 wiring summary:

```text
GPIO17 ---- R2 4.7k ---- Q1 pin 2 / Base
                          |
                        R3 100k
                          |
GND ----------------------+

Q1 pin 1 / Emitter   ---- GND
Q1 pin 3 / Collector ---- Fan PWM pin 4
```

Fan wiring for this test:

| Fan Pin | Signal | Breadboard Connection |
|---------|--------|-----------------------|
| 1 | GND | GND / blue rail |
| 2 | +12 V | +12 V supply |
| 3 | Tach / RPM sense | Leave disconnected for Q1-only PWM test |
| 4 | PWM control | Q1 collector / pin 3 |

The Raspberry Pi GND, 12 V supply GND, fan GND, and Q1 emitter GND must all be connected together.

To test PWM from the Raspberry Pi, run:

```bash
sudo apt install -y python3-lgpio
/usr/bin/python3 scripts/fan_pwm_sweep.py
```

The test uses BCM GPIO17 at 10 kHz and sweeps the requested fan speed from 95% down to 20% and back up in a loop, holding each step for 5 seconds. Because Q1 inverts the signal, the script handles the inversion internally.

## Before Fabrication

- Confirm the exact XY3606 module wiring and terminal polarity before powering the Raspberry Pi.
- Confirm J1 current rating is sufficient for fan + Raspberry Pi load.
- Choose exact connector part numbers and replace remaining placeholder footprints where needed.
- Use the default fan tach population: `R4=10k`, `R5=1k`.
- Run KiCad ERC/DRC after assigning final footprints and routing.
