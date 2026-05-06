from __future__ import annotations

from dataclasses import dataclass
from time import sleep

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover
    SMBus = None


SHT30_I2C_ADDRESS = 0x44
SHT30_MEASURE_HIGH_REPEATABILITY = [0x2C, 0x06]

QMP6988_I2C_ADDRESS = 0x70
QMP6988_CHIP_ID_REG = 0xD1
QMP6988_CHIP_ID = 0x5C
QMP6988_STATUS_REG = 0xF3
QMP6988_CTRL_REG = 0xF4
QMP6988_ADC_DATA_REG = 0xF7
QMP6988_OTP_BASE = 0xA0


@dataclass
class EnvironmentalData:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float

    def to_dict(self) -> dict[str, float]:
        return {
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "pressure_hpa": self.pressure_hpa,
        }


class EnvIIIUnit:
    """Raspberry Pi adapter for M5Stack ENV III Unit (SHT30 + QMP6988 sensors).

    Connect the ENV III unit to the Raspberry Pi I2C pins:
      - SDA -> GPIO2
      - SCL -> GPIO3
      - 5V -> 5V
      - GND -> GND

    Sensors:
      - SHT30 at I2C address 0x44 (temperature & humidity)
      - QMP6988 at I2C address 0x70 (pressure)
    """

    def __init__(self, i2c_bus: int = 1):
        self.i2c_bus = i2c_bus
        self.bus = None
        self.qmp6988_cal = None

        if SMBus is None:
            print("Warning: smbus2 is not installed. ENV III sensors will not be available.")
            return

        try:
            self.bus = SMBus(i2c_bus)
            print(f"ENV III sensors initialized on I2C bus {i2c_bus}")
            self._init_qmp6988()
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

    def _init_qmp6988(self) -> None:
        """Initialize QMP6988 pressure sensor and read calibration data."""
        if self.bus is None:
            return

        try:
            chip_id = self.bus.read_byte_data(QMP6988_I2C_ADDRESS, QMP6988_CHIP_ID_REG)
            if chip_id != QMP6988_CHIP_ID:
                print(
                    f"Warning: QMP6988 chip ID mismatch. Expected 0x{QMP6988_CHIP_ID:02X}, got 0x{chip_id:02X}"
                )
                return

            self.qmp6988_cal = self._read_qmp6988_calibration()
            if self.qmp6988_cal:
                print("QMP6988 pressure sensor initialized")
            else:
                print("Failed to read QMP6988 calibration data")
        except Exception as exc:
            print(f"QMP6988 initialization error: {exc}")

    def _read_qmp6988_calibration(self) -> dict | None:
        """Read QMP6988 calibration coefficients from OTP memory."""
        try:
            otp_data = self.bus.read_i2c_block_data(
                QMP6988_I2C_ADDRESS, QMP6988_OTP_BASE, 26
            )

            return {
                "c0": ((otp_data[0] & 0x3F) << 4) | ((otp_data[1] & 0xF0) >> 4),
                "c1": ((otp_data[1] & 0x0F) << 8) | otp_data[2],
                "c2": (otp_data[3] << 8) | otp_data[4],
                "c3": (otp_data[5] << 8) | otp_data[6],
                "c4": ((otp_data[7] & 0x0F) << 8) | otp_data[8],
                "c5": (otp_data[9] << 8) | otp_data[10],
                "c6": (otp_data[11] << 8) | otp_data[12],
                "c7": (otp_data[13] << 8) | otp_data[14],
                "c8": (otp_data[15] << 8) | otp_data[16],
                "c9": (otp_data[17] << 8) | otp_data[18],
                "ca": (otp_data[19] << 8) | otp_data[20],
                "cb": (otp_data[21] << 8) | otp_data[22],
                "cc": (otp_data[23] << 8) | otp_data[24],
                "d1": otp_data[25] & 0x0F,
            }
        except Exception as exc:
            print(f"Error reading QMP6988 calibration: {exc}")
            return None

    def _read_qmp6988_pressure(self) -> float | None:
        """Read pressure from QMP6988 sensor."""
        if self.bus is None or self.qmp6988_cal is None:
            return None

        try:
            self.bus.write_byte_data(QMP6988_I2C_ADDRESS, QMP6988_CTRL_REG, 0x33)
            sleep(0.008)

            adc_data = self.bus.read_i2c_block_data(
                QMP6988_I2C_ADDRESS, QMP6988_ADC_DATA_REG, 3
            )

            adc_p = (adc_data[0] << 16) | (adc_data[1] << 8) | adc_data[2]
            adc_p = adc_p >> 4

            cal = self.qmp6988_cal
            c0 = cal["c0"] if cal["c0"] < 32768 else cal["c0"] - 65536
            c1 = cal["c1"] if cal["c1"] < 32768 else cal["c1"] - 65536
            c2 = cal["c2"] if cal["c2"] < 32768 else cal["c2"] - 65536
            c3 = cal["c3"] if cal["c3"] < 32768 else cal["c3"] - 65536
            c4 = cal["c4"] if cal["c4"] < 32768 else cal["c4"] - 65536
            c5 = cal["c5"] if cal["c5"] < 32768 else cal["c5"] - 65536
            c6 = cal["c6"] if cal["c6"] < 32768 else cal["c6"] - 65536
            c7 = cal["c7"] if cal["c7"] < 32768 else cal["c7"] - 65536
            c8 = cal["c8"] if cal["c8"] < 32768 else cal["c8"] - 65536
            c9 = cal["c9"] if cal["c9"] < 32768 else cal["c9"] - 65536
            ca = cal["ca"] if cal["ca"] < 32768 else cal["ca"] - 65536
            cb = cal["cb"] if cal["cb"] < 32768 else cal["cb"] - 65536
            cc = cal["cc"] if cal["cc"] < 32768 else cal["cc"] - 65536

            opa = c0 + (c1 + 261.0) * adc_p / 65536.0
            opb = opa + (c2 + adc_p / 32.0) * adc_p / 524288.0

            pressure_pa = opb + ((c3 + 0.5) / 128.0) * adc_p / 16777216.0
            pressure_hpa = pressure_pa / 100.0

            return pressure_hpa
        except Exception as exc:
            print(f"Error reading QMP6988 pressure: {exc}")
            return None

    def read_environment(self) -> EnvironmentalData:
        if self.bus is None:
            return EnvironmentalData(
                temperature_c=22.4,
                humidity_pct=43.2,
                pressure_hpa=1013.25,
            )

        temperature_c = 0.0
        humidity_pct = 0.0
        pressure_hpa = 0.0

        try:
            temperature_raw, humidity_raw = self._read_raw_measurement()
            temperature_c = self._convert_temperature(temperature_raw)
            humidity_pct = self._convert_humidity(humidity_raw)
        except Exception as exc:
            print(f"Error reading SHT30 sensor: {exc}")

        pressure_read = self._read_qmp6988_pressure()
        if pressure_read is not None:
            pressure_hpa = pressure_read
        else:
            pressure_hpa = 0.0

        print(
            f"DEBUG: SHT30 read - temp={temperature_c:.2f}°C, humidity={humidity_pct:.2f}% | "
            f"QMP6988 read - pressure={pressure_hpa:.2f} hPa"
        )

        return EnvironmentalData(
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            pressure_hpa=pressure_hpa,
        )

    def close(self) -> None:
        """Close the I2C bus connection."""
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass


def create_env_unit(i2c_bus: int = 1) -> EnvIIIUnit:
    return EnvIIIUnit(i2c_bus=i2c_bus)
