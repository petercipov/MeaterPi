# MeaterPi PCB

KiCad starter project for a Raspberry Pi Zero 2 W carrier board.

## Design Intent

- One 12 V DC barrel jack input for the fan and 5 V Raspberry Pi rail
- Input protection:
  - 1206 SMD resettable polyfuse
  - P-channel MOSFET reverse-polarity protection
  - TVS diode on the protected 12 V rail
  - bulk input capacitor
  - 100 nF ceramic input capacitor
- Buck converter module footprint placeholder for 12 V to 5 V
- 40-pin Raspberry Pi GPIO header
- M5Stack ENV III HY2.0/Grove-style 4-pin connector
- 4-pin PC PWM fan connector
- Open-drain fan PWM driver from GPIO17
- Fan tach/RPM path to GPIO27

## Reference Designator Shortcuts

These are the short labels printed on the schematic/PCB:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `C` | Capacitor | `C1` bulk input capacitor |
| `D` | Diode | `D1` TVS protection diode |
| `F` | Fuse or resettable fuse | `F1` input polyfuse |
| `J` | Connector/header/jack | `J1` 12 V barrel jack |
| `Q` | Transistor or MOSFET | `Q1` PWM MOSFET |
| `R` | Resistor | `R2` PWM gate resistor |
| `U` | Module or IC | `U1` buck converter module |

## Component Reference

| Ref | Value / Part | Purpose |
|-----|--------------|---------|
| `J1` | `12V_BARREL_JACK` | Horizontal DC barrel jack input. Current footprint is CUI PJ-063AH-style, 5.5 mm OD / 2.0 mm ID, center-positive. Pin 1 is +12 V input, pin 2 is GND/sleeve. |
| `F1` | SMD polyfuse | Resettable input fuse for the incoming 12 V rail. Choose final current rating before fabrication. |
| `Q2` | `PMOS_REV_PROTECT` | P-channel MOSFET used for reverse-polarity input protection. Verify the exact pinout for the selected part. |
| `R7` | 100k | Gate pull-down for the reverse-polarity PMOS protection circuit. |
| `D1` | `SMBJ15A` | TVS diode that clamps transients on the protected 12 V rail. |
| `C1` | 220 uF / 25 V | Bulk input capacitor on the protected 12 V rail. |
| `C2` | 100 nF | Small ceramic bypass capacitor on the protected 12 V rail. |
| `U1` | `5V_BUCK_MODULE` | Placeholder footprint for a 12 V to 5 V buck converter module. |
| `J2` | `RASPBERRY_PI_GPIO` | 40-pin Raspberry Pi GPIO socket/header connection. |
| `J3` | `ENV_III` | 4-pin HY2.0/Grove-style connector for the M5Stack ENV III sensor. |
| `J4` | `4PIN_PWM_FAN` | Standard 4-pin PC PWM fan connector. |
| `Q1` | `2N7002` | N-channel MOSFET used as the open-drain PWM driver for fan pin 4. |
| `R2` | 220R | Series resistor between Raspberry Pi GPIO17 and the Q1 gate. |
| `R3` | 100k | Pull-down resistor for the Q1 gate, keeping fan PWM off during boot/reset. |
| `R4` | 10k DNP | Optional 3.3 V pull-up for fan tach if the fan tach output is open-drain/open-collector. Do not populate when using the divider option. |
| `R5` | 1k | Upper resistor in the fan tach divider path. |
| `R6` | 2k | Lower resistor in the fan tach divider path to scale tach voltage for GPIO27. |
| `C3` | 100 nF | 5 V rail bypass capacitor near the Raspberry Pi/buck output. |

## Important Pin Assumptions

### Power Jack

J1 assumes a center-positive 12 V DC barrel jack:

| Pin | Signal |
|-----|--------|
| 1 | +12V center pin / tip |
| 2 | GND sleeve |
| MP | Mechanical mounting pads, not connected |

### Fan Header

Standard 4-pin PC PWM fan convention:

| Pin | Signal |
|-----|--------|
| 1 | GND |
| 2 | +12V |
| 3 | Tach / RPM sense |
| 4 | PWM control |

### ENV III Connector

M5Stack ENV III PORT.A convention:

| Pin | Wire | Signal |
|-----|------|--------|
| 1 | Black | GND |
| 2 | Red | 5V |
| 3 | Yellow | SDA |
| 4 | White | SCL |

## Before Fabrication

- Confirm the exact J1 barrel jack part before fabrication. The current layout targets a CUI PJ-063AH-style horizontal jack.
- Choose exact connector part numbers and replace remaining placeholder footprints where needed.
- Choose the exact 1206 polyfuse current rating for the 12 V input.
- Choose the buck converter module footprint or replace it with an onboard regulator design.
- Review the PMOS reverse-polarity circuit for the selected MOSFET pinout.
- Decide the tach circuit population option:
  - use the 1k/2k divider if the fan tach line is externally/internally pulled to about 5 V
  - use the optional 3.3 V pullup instead if the fan tach output is open-drain/open-collector
- Run KiCad ERC/DRC after assigning final footprints.
