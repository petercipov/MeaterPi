from __future__ import annotations

from dataclasses import dataclass
from time import sleep

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover
    SMBus = None


SHT30_I2C_ADDRESS = 0x44
SHT30_MEASURE_HIGH_REPEATABILITY = [0x2C, 0x06]


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
        self.bus = None

        if SMBus is None:
            print("Warning: smbus2 is not installed. SHT30 sensor will not be available.")
            return

        try:
            self.bus = SMBus(i2c_bus)
            print(f"SHT30 sensor initialized on I2C bus {i2c_bus}")
        except Exception as exc:
            print(f"Failed to open I2C bus {i2c_bus}: {exc}")
            self.bus = None

    def _crc8(self, data: bytes) -> int:
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc << 1) ^ 0x31 if crc & 0x80 else crc << 1
                crc &= 0xFF
        return crc

    def _read_raw_measurement(self) -> tuple[int, int]:
        if self.bus is None:
            raise RuntimeError("I2C bus is unavailable")

        self.bus.write_i2c_block_data(
            SHT30_I2C_ADDRESS,
            SHT30_MEASURE_HIGH_REPEATABILITY[0],
            [SHT30_MEASURE_HIGH_REPEATABILITY[1]],
        )
        sleep(0.015)
        raw = self.bus.read_i2c_block_data(SHT30_I2C_ADDRESS, 0x00, 6)

        temperature_raw = (raw[0] << 8) | raw[1]
        temperature_crc = raw[2]
        humidity_raw = (raw[3] << 8) | raw[4]
        humidity_crc = raw[5]

        if self._crc8(bytes(raw[0:2])) != temperature_crc:
            raise ValueError("SHT30 temperature CRC mismatch")
        if self._crc8(bytes(raw[3:5])) != humidity_crc:
            raise ValueError("SHT30 humidity CRC mismatch")

        return temperature_raw, humidity_raw

    @staticmethod
    def _convert_temperature(raw: int) -> float:
        return -45.0 + (175.0 * raw / 65535.0)

    @staticmethod
    def _convert_humidity(raw: int) -> float:
        return 100.0 * raw / 65535.0

    def read_environment(self) -> EnvironmentalData:
        if self.bus is None:
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
            )

        try:
            temperature_raw, humidity_raw = self._read_raw_measurement()
            temperature_c = self._convert_temperature(temperature_raw)
            humidity_pct = self._convert_humidity(humidity_raw)

            print(
                f"DEBUG: SHT30 read - temp={temperature_c:.2f}°C, humidity={humidity_pct:.2f}%"
            )

            return EnvironmentalData(
                temperature_c=temperature_c,
                humidity_pct=humidity_pct,
            )
        except Exception as exc:
            print(f"Error reading SHT30 sensor: {exc}")
            return EnvironmentalData(
                temperature_c=0.0,
                humidity_pct=0.0,
            )

    def close(self) -> None:
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass


def create_env_unit(i2c_bus: int = 1) -> EnvIIIUnit:
    return EnvIIIUnit(i2c_bus=i2c_bus)
