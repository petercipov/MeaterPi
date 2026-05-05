import time

from .env3 import EnvIIIUnit


def main() -> None:
    unit = EnvIIIUnit(i2c_bus=1)
    print("Starting MeaterPi ENV III reader")

    try:
        addresses = unit.scan_i2c_bus()
        if addresses:
            print("Detected I2C addresses:", [hex(addr) for addr in addresses])
        else:
            print("No I2C devices detected on bus 1.")
    except RuntimeError as exc:
        print(f"I2C scan skipped: {exc}")

    while True:
        data = unit.read_environment()
        values = data.to_dict()
        print("ENV III values:")
        for key, value in values.items():
            print(f"  {key}: {value}")
        print("---")
        time.sleep(5)


if __name__ == "__main__":
    main()
