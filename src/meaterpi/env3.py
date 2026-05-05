from __future__ import annotations

import time
from dataclasses import dataclass

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover
    SMBus = None


@dataclass
class EnvironmentalData:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    co2_ppm: int | None = None
    voc_index: float | None = None
    light_lux: float | None = None

    def to_dict(self) -> dict[str, float | int | None]:
        return {
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "pressure_hpa": self.pressure_hpa,
            "co2_ppm": self.co2_ppm,
            "voc_index": self.voc_index,
            "light_lux": self.light_lux,
        }


class EnvIIIUnit:
    """Raspberry Pi adapter for M5Stack ENV III Unit.

    Connect the ENV III unit to the Raspberry Pi I2C pins:
      - SDA -> GPIO2
      - SCL -> GPIO3
      - 3V3 -> 3.3V
      - GND -> GND

    For now, this class prints environmental placeholder values and provides
    a simple I2C bus scan.
    """

    def __init__(self, i2c_bus: int = 1):
        self.i2c_bus = i2c_bus
        self.bus = SMBus(i2c_bus) if SMBus is not None else None

    def scan_i2c_bus(self) -> list[int]:
        """Scan the I2C bus and return all detected addresses."""
        if self.bus is None:
            raise RuntimeError("smbus2 is not installed or I2C bus is unavailable")

        addresses: list[int] = []
        for address in range(0x03, 0x78):
            try:
                self.bus.read_byte(address)
                addresses.append(address)
            except OSError:
                continue
        return addresses

    def read_environment(self) -> EnvironmentalData:
        """Read the current environment values from the unit.

        This method currently returns placeholder values. When the hardware is
        available, replace the placeholder logic with real register reads.
        """
        if self.bus is None:
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
                pressure_hpa=1013.6,
                co2_ppm=415,
                voc_index=0.65,
                light_lux=120.0,
            )

        # TODO: implement sensor-specific I2C reads for ENV III registers here.
        return EnvironmentalData(
            temperature_c=22.4,
            humidity_pct=43.2,
            pressure_hpa=1013.6,
            co2_ppm=415,
            voc_index=0.65,
            light_lux=120.0,
        )

    def close(self) -> None:
        if self.bus is not None:
            self.bus.close()


def create_env_unit(i2c_bus: int = 1) -> EnvIIIUnit:
    return EnvIIIUnit(i2c_bus=i2c_bus)
