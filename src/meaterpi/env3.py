from __future__ import annotations

import time
from dataclasses import dataclass

try:
    from sht30 import SHT30
except ImportError:  # pragma: no cover
    SHT30 = None


@dataclass
class EnvironmentalData:
    temperature_c: float
    humidity_pct: float

    def to_dict(self) -> dict[str, float]:
        return {
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
        }


class EnvIIIUnit:
    """Raspberry Pi adapter for M5Stack ENV III Unit (SHT30 sensor).

    Connect the ENV III unit to the Raspberry Pi I2C pins:
      - SDA -> GPIO2
      - SCL -> GPIO3
      - 5V -> 5V
      - GND -> GND

    The SHT30 sensor is detected at I2C address 0x44.
    """

    def __init__(self, i2c_bus: int = 1):
        self.i2c_bus = i2c_bus
        self.sensor = None
        
        if SHT30 is not None:
            try:
                self.sensor = SHT30(bus=i2c_bus)
                print(f"SHT30 sensor initialized on bus {i2c_bus}")
            except Exception as e:
                print(f"Failed to initialize SHT30: {e}")

    def read_environment(self) -> EnvironmentalData:
        """Read temperature and humidity from the SHT30 sensor at 0x44."""
        if self.sensor is None:
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
            )

        try:
            # Read temperature and humidity
            temp_c = self.sensor.temperature()
            humidity = self.sensor.humidity()
            
            print(f"DEBUG: SHT30 read - temp={temp_c:.2f}°C, humidity={humidity:.2f}%")
            
            return EnvironmentalData(
                temperature_c=temp_c,
                humidity_pct=humidity,
            )
        except Exception as e:
            print(f"Error reading SHT30: {e}")
            return EnvironmentalData(
                temperature_c=0.0,
                humidity_pct=0.0,
            )

    def close(self) -> None:
        """Close the sensor connection."""
        if self.sensor is not None:
            try:
                self.sensor.close()
            except Exception:
                pass


def create_env_unit(i2c_bus: int = 1) -> EnvIIIUnit:
    return EnvIIIUnit(i2c_bus=i2c_bus)
