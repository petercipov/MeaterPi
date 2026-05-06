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
    altitude_m: float

    def to_dict(self) -> dict[str, float]:
        return {
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "pressure_hpa": self.pressure_hpa,
            "altitude_m": self.altitude_m,
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
        """Read QMP6988 calibration coefficients from OTP memory (0xA0-0xB8)."""
        try:
            otp_data = self.bus.read_i2c_block_data(
                QMP6988_I2C_ADDRESS, QMP6988_OTP_BASE, 25
            )

            def to_signed_16(val: int) -> int:
                return val if val < 32768 else val - 65536

            def to_signed_20(val: int) -> int:
                return val if val < (1 << 19) else val - (1 << 20)

            b00_raw = ((otp_data[0] << 12) | (otp_data[1] << 4) | ((otp_data[24] & 0xF0) >> 4))
            a0_raw = ((otp_data[18] << 12) | (otp_data[19] << 4) | (otp_data[24] & 0x0F))

            b00 = to_signed_20(b00_raw)
            a0 = to_signed_20(a0_raw)

            return {
                "b00": b00,
                "bt1": 2982 * to_signed_16(self._bytes_to_int16(otp_data[2], otp_data[3])) + 107370906,
                "bt2": 329854 * to_signed_16(self._bytes_to_int16(otp_data[4], otp_data[5])) + 108083093,
                "bp1": 19923 * to_signed_16(self._bytes_to_int16(otp_data[6], otp_data[7])) + 1133836764,
                "b11": 2406 * to_signed_16(self._bytes_to_int16(otp_data[8], otp_data[9])) + 118215883,
                "bp2": 3079 * to_signed_16(self._bytes_to_int16(otp_data[10], otp_data[11])) - 181579595,
                "b12": 6846 * to_signed_16(self._bytes_to_int16(otp_data[12], otp_data[13])) + 85590281,
                "b21": 13836 * to_signed_16(self._bytes_to_int16(otp_data[14], otp_data[15])) + 79333336,
                "bp3": 2915 * to_signed_16(self._bytes_to_int16(otp_data[16], otp_data[17])) + 157155561,
                "a0": a0,
                "a1": 3608 * self._bytes_to_int16(otp_data[20], otp_data[21]) - 1731677965,
                "a2": 16889 * self._bytes_to_int16(otp_data[22], otp_data[23]) - 87619360,
            }
        except Exception as exc:
            print(f"Error reading QMP6988 calibration: {exc}")
            return None

    @staticmethod
    def _bytes_to_int16(high: int, low: int) -> int:
        val = (high << 8) | low
        return val if val < 32768 else val - 65536

    @staticmethod
    def _signed_divide(dividend: int, divisor: int) -> int:
        quotient = abs(dividend) // divisor
        return quotient if dividend >= 0 else -quotient

    def _read_qmp6988_pressure(self) -> float | None:
        """Read pressure from QMP6988 sensor using full M5Stack fixed-point conversion."""
        if self.bus is None or self.qmp6988_cal is None:
            return None

        try:
            # Trigger measurement (control register 0xF4 = 0x33 for normal mode)
            self.bus.write_byte_data(QMP6988_I2C_ADDRESS, QMP6988_CTRL_REG, 0x33)
            sleep(0.008)

            # Read 6 bytes: pressure (0xF7-0xF9) then temperature (0xFA-0xFC)
            adc_data = self.bus.read_i2c_block_data(
                QMP6988_I2C_ADDRESS, QMP6988_ADC_DATA_REG, 6
            )

            # Parse raw data: pressure in bytes[0:3], temperature in bytes[3:6]
            pressure_raw = (adc_data[0] << 16) | (adc_data[1] << 8) | adc_data[2]
            temp_raw = (adc_data[3] << 16) | (adc_data[4] << 8) | adc_data[5]

            # Subtract offset (2^23 = 8388608)
            SUB_RAW = 8388608
            dp = int(pressure_raw) - SUB_RAW
            dt = int(temp_raw) - SUB_RAW

            # Convert temperature first (needed for pressure compensation)
            t256 = self._convert_qmp6988_temperature(dt)

            # Convert pressure using temperature-compensated formula
            p16 = self._convert_qmp6988_pressure(dp, t256)

            # Final conversion: Pa from Q4 format, then to hPa
            pressure_pa = p16 / 16.0
            pressure_hpa = pressure_pa / 100.0

            qmp_temp_c = t256 / 256.0
            print(
                f"DEBUG QMP6988 raw: pressure_raw={pressure_raw} temp_raw={temp_raw} dt={dt} "
                f"t256={t256} temp_int={qmp_temp_c:.2f} p16={p16} pressure_pa={pressure_pa:.2f} "
                f"pressure_hpa={pressure_hpa:.4f}"
            )

            return pressure_hpa

        except Exception as exc:
            print(f"Error reading QMP6988 pressure: {exc}")
            return None

    def _convert_qmp6988_temperature(self, dt: int) -> int:
        """Convert raw temperature using M5Stack fixed-point algorithm."""
        c = self.qmp6988_cal

        wk1 = c["a1"] * dt
        wk2 = (c["a2"] * dt) >> 14
        wk2 = (wk2 * dt) >> 10
        wk2 = self._signed_divide(wk1 + wk2, 32767) >> 19
        temp256 = (c["a0"] + wk2) >> 4
        return int(temp256)

    def _convert_qmp6988_pressure(self, dp: int, tx: int) -> int:
        """Convert raw pressure using M5Stack fixed-point algorithm with temperature compensation."""
        c = self.qmp6988_cal

        wk1 = c["bt1"] * tx
        wk2 = (c["bp1"] * dp) >> 5
        wk1 += wk2

        wk2 = (c["bt2"] * tx) >> 1
        wk2 = (wk2 * tx) >> 8
        wk3 = wk2

        wk2 = (c["b11"] * tx) >> 4
        wk2 = (wk2 * dp) >> 1
        wk3 += wk2

        wk2 = (c["bp2"] * dp) >> 13
        wk2 = (wk2 * dp) >> 1
        wk3 += wk2

        wk1 += wk3 >> 14

        wk2 = c["b12"] * tx
        wk2 = (wk2 * tx) >> 22
        wk2 = (wk2 * dp) >> 1
        wk3 = wk2

        wk2 = (c["b21"] * tx) >> 6
        wk2 = (wk2 * dp) >> 23
        wk2 = (wk2 * dp) >> 1
        wk3 += wk2

        wk2 = (c["bp3"] * dp) >> 12
        wk2 = (wk2 * dp) >> 23
        wk2 = wk2 * dp
        wk3 += wk2

        wk1 += wk3 >> 15
        wk1 = self._signed_divide(wk1, 32767)
        wk1 >>= 11
        wk1 += c["b00"]
        return int(wk1)

    @staticmethod
    def _calc_altitude(pressure_hpa: float, temperature_c: float) -> float:
        """Calculate altitude in meters from pressure and temperature."""
        pressure_pa = pressure_hpa * 100.0
        return (
            (pow(101325.0 / pressure_pa, 1.0 / 5.257) - 1.0)
            * (temperature_c + 273.15)
            / 0.0065
        )

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

        altitude_m = self._calc_altitude(pressure_hpa, temperature_c) if pressure_hpa > 0 else 0.0

        print(
            f"DEBUG: SHT30 read - temp={temperature_c:.2f}°C, humidity={humidity_pct:.2f}% | "
            f"QMP6988 read - pressure={pressure_hpa:.2f} hPa | altitude={altitude_m:.1f} m"
        )

        return EnvironmentalData(
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            pressure_hpa=pressure_hpa,
            altitude_m=altitude_m,
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
