import time

from .env3 import EnvIIIUnit


def main() -> None:
    unit = EnvIIIUnit(i2c_bus=1)
    print("Starting MeaterPi ENV III reader")

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
