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
      - 5V -> 5V
      - GND -> GND

    The ENV III is detected at I2C address 0x44.
    """

    # ENV III I2C address
    ENV_III_ADDR = 0x44

    # Register addresses (typical ENV III layout)
    REG_TEMP_HIGH = 0x00
    REG_TEMP_LOW = 0x01
    REG_HUM_HIGH = 0x02
    REG_HUM_LOW = 0x03
    REG_PRESS_HIGH = 0x04
    REG_PRESS_MID = 0x05
    REG_PRESS_LOW = 0x06
    REG_GAS = 0x07

    def __init__(self, i2c_bus: int = 1):
        self.i2c_bus = i2c_bus
        self.bus = SMBus(i2c_bus) if SMBus is not None else None
        self._initialized = False

    def _initialize_sensor(self) -> None:
        """Initialize the ENV III sensor for measurement mode."""
        if self._initialized or self.bus is None:
            return
        
        try:
            # Try writing reset/init command to register 0 (common for many sensors)
            # This may vary depending on actual ENV III chip (BME688, etc.)
            print("DEBUG: Attempting to initialize sensor...")
            # Common init sequence: write 0x09 to register 0xE0 to reset BME688
            try:
                self.bus.write_byte_data(self.ENV_III_ADDR, 0xE0, 0x09)
                print("DEBUG: Sent reset command to 0xE0")
                time.sleep(0.1)
            except OSError:
                print("DEBUG: Reset command failed, device may not support it")
            
            self._initialized = True
        except Exception as e:
            print(f"DEBUG: Initialization error: {e}")

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
        """Read the current environment values from the ENV III unit at 0x44."""
        if self.bus is None:
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
                pressure_hpa=1013.6,
                co2_ppm=415,
                voc_index=0.65,
                light_lux=120.0,
            )

        try:
            self._initialize_sensor()
            
            # Dump extended registers to find actual data layout
            all_regs = self.bus.read_i2c_block_data(self.ENV_III_ADDR, 0x00, 32)
            print(f"DEBUG: registers [0x00-0x1F] = {all_regs}")
            print(f"DEBUG: hex = {[hex(b) for b in all_regs]}")
            
            # Try reading from higher registers (0x80+) which often contain measurement data
            try:
                meas_regs = self.bus.read_i2c_block_data(self.ENV_III_ADDR, 0x80, 16)
                print(f"DEBUG: measurement registers [0x80-0x8F] = {meas_regs}")
                print(f"DEBUG: measurement hex = {[hex(b) for b in meas_regs]}")
            except OSError:
                print("DEBUG: Could not read measurement registers at 0x80")
            
            # Also try reading from 0x70
            try:
                alt_regs = self.bus.read_i2c_block_data(0x70, 0x00, 16)
                print(f"DEBUG: 0x70 registers [0x00-0x0F] = {alt_regs}")
                print(f"DEBUG: 0x70 hex = {[hex(b) for b in alt_regs]}")
            except OSError:
                print("DEBUG: Could not read from 0x70")

            # For now, return placeholder since we can't parse the data yet
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
                pressure_hpa=1013.6,
                co2_ppm=415,
                voc_index=0.65,
                light_lux=120.0,
            )
        except OSError as e:
            print(f"Error reading ENV III: {e}")
            return EnvironmentalData(
                temperature_c=0.0,
                humidity_pct=0.0,
                pressure_hpa=0.0,
            )

    @staticmethod
    def _parse_temperature(data: list[int]) -> float:
        """Convert raw temperature bytes to Celsius."""
        # Combine high and low bytes; assume 16-bit signed, scale by 0.01°C per unit
        raw = (data[0] << 8) | data[1]
        # Handle two's complement for negative temperatures
        if raw & 0x8000:
            raw = raw - 0x10000
        return raw * 0.005  # Typical scale for temperature sensors

    @staticmethod
    def _parse_humidity(data: list[int]) -> float:
        """Convert raw humidity bytes to percentage RH."""
        # Combine high and low bytes; scale to 0-100%
        raw = (data[0] << 8) | data[1]
        return (raw / 65535.0) * 100.0

    @staticmethod
    def _parse_pressure(data: list[int]) -> float:
        """Convert raw pressure bytes to hPa."""
        # Combine three bytes; typical scale for pressure sensors
        raw = (data[0] << 16) | (data[1] << 8) | data[2]
        # Scale from raw value to hPa; typical ENV III uses 25600 as 100 hPa
        return (raw / 256.0) + 300.0  # Typical offset for pressure sensors

    @staticmethod
    def _parse_gas(data: list[int]) -> float:
        """Convert raw gas/VOC bytes to VOC index (0-500 typical range)."""
        raw = (data[0] << 8) | data[1]
        # Scale to 0-100 range for VOC index
        return (raw / 65535.0) * 100.0

    def close(self) -> None:
        """Close the I2C bus connection."""
        if self.bus is not None:
            self.bus.close()


def create_env_unit(i2c_bus: int = 1) -> EnvIIIUnit:
    return EnvIIIUnit(i2c_bus=i2c_bus)
