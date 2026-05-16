#!/usr/bin/env python3
"""Simple GPIO17 fan PWM test for the MeaterPi Q1 breadboard circuit."""

import time

import lgpio


GPIO_CHIP = 0
FAN_PWM_GPIO = 17
PWM_FREQUENCY_HZ = 10_000

MIN_FAN_PERCENT = 20
MAX_FAN_PERCENT = 100
STEP_PERCENT = 5
STEP_DELAY_SECONDS = 1


def set_fan_percent(chip, fan_percent):
    # Q1 inverts the signal: GPIO high pulls fan PWM low.
    gpio_percent = 100 - fan_percent

    if gpio_percent <= 0:
        lgpio.tx_pwm(chip, FAN_PWM_GPIO, 0, 0)
        lgpio.gpio_write(chip, FAN_PWM_GPIO, 0)
    elif gpio_percent >= 100:
        lgpio.tx_pwm(chip, FAN_PWM_GPIO, 0, 0)
        lgpio.gpio_write(chip, FAN_PWM_GPIO, 1)
    else:
        lgpio.tx_pwm(chip, FAN_PWM_GPIO, PWM_FREQUENCY_HZ, gpio_percent)


def main():
    chip = lgpio.gpiochip_open(GPIO_CHIP)

    try:
        lgpio.gpio_claim_output(chip, FAN_PWM_GPIO, 0)
        print(f"Sweeping fan PWM on BCM GPIO17 at {PWM_FREQUENCY_HZ} Hz.")
        print("Press Ctrl-C to stop.")

        while True:
            for fan_percent in range(MAX_FAN_PERCENT, MIN_FAN_PERCENT - 1, -STEP_PERCENT):
                set_fan_percent(chip, fan_percent)
                print(f"Fan PWM request: {fan_percent}%")
                time.sleep(STEP_DELAY_SECONDS)

            for fan_percent in range(MIN_FAN_PERCENT, MAX_FAN_PERCENT + 1, STEP_PERCENT):
                set_fan_percent(chip, fan_percent)
                print(f"Fan PWM request: {fan_percent}%")
                time.sleep(STEP_DELAY_SECONDS)

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        set_fan_percent(chip, 100)
        lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    main()
