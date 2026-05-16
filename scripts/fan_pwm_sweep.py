#!/usr/bin/env python3
"""Simple GPIO17 fan PWM test for the MeaterPi Q1 breadboard circuit."""

import threading
import time

import lgpio


GPIO_CHIP = 0
FAN_PWM_GPIO = 17
FAN_TACH_GPIO = 27
PWM_FREQUENCY_HZ = 10_000

MIN_FAN_PERCENT = 10
MAX_FAN_PERCENT = 100
STEP_PERCENT = 5
STEP_DELAY_SECONDS = 5
OFF_DELAY_SECONDS = 5
TACH_PULSES_PER_REVOLUTION = 2

tach_pulses = 0
tach_lock = threading.Lock()


def count_tach_pulse(chip, gpio, level, tick):
    del chip, gpio, tick

    if level != 0:
        return

    global tach_pulses
    with tach_lock:
        tach_pulses += 1


def reset_tach_pulses():
    global tach_pulses
    with tach_lock:
        tach_pulses = 0


def read_tach_pulses():
    with tach_lock:
        return tach_pulses


def set_fan_percent(chip, fan_percent):
    if fan_percent >= 100:
        # 100% fan request: Q1 is off, fan PWM input is released.
        lgpio.gpio_write(chip, FAN_PWM_GPIO, 0)
        return

    if fan_percent <= 0:
        turn_fan_off(chip)
        return

    # Q1 inverts the signal: GPIO high pulls fan PWM low.
    gpio_percent = 100 - fan_percent
    lgpio.tx_pwm(chip, FAN_PWM_GPIO, PWM_FREQUENCY_HZ, gpio_percent)


def turn_fan_off(chip):
    # 0% fan request: Q1 pulls the fan PWM input low.
    lgpio.gpio_write(chip, FAN_PWM_GPIO, 1)


def measure_rpm_for(seconds):
    reset_tach_pulses()
    start = time.monotonic()
    time.sleep(seconds)
    elapsed = time.monotonic() - start
    pulses = read_tach_pulses()
    rpm = (pulses / TACH_PULSES_PER_REVOLUTION) * (60 / elapsed)
    return round(rpm), pulses


def print_step_result(fan_percent, seconds):
    rpm, pulses = measure_rpm_for(seconds)
    print(f"Fan PWM request: {fan_percent:3d}%, RPM: {rpm:4d}, tach pulses: {pulses}")


def main():
    chip = lgpio.gpiochip_open(GPIO_CHIP)
    tach_callback = None

    try:
        lgpio.gpio_claim_output(chip, FAN_PWM_GPIO, 0)
        lgpio.gpio_claim_alert(chip, FAN_TACH_GPIO, lgpio.FALLING_EDGE, lgpio.SET_PULL_NONE)
        tach_callback = lgpio.callback(chip, FAN_TACH_GPIO, lgpio.FALLING_EDGE, count_tach_pulse)

        print(f"Sweeping fan PWM on BCM GPIO{FAN_PWM_GPIO} at {PWM_FREQUENCY_HZ} Hz.")
        print(f"Reading fan tach on BCM GPIO{FAN_TACH_GPIO}.")
        print("Press Ctrl-C to stop.")

        while True:
            for fan_percent in range(MAX_FAN_PERCENT, MIN_FAN_PERCENT - 1, -STEP_PERCENT):
                set_fan_percent(chip, fan_percent)
                print_step_result(fan_percent, STEP_DELAY_SECONDS)

            turn_fan_off(chip)
            print_step_result(0, OFF_DELAY_SECONDS)

            for fan_percent in range(MIN_FAN_PERCENT, MAX_FAN_PERCENT + 1, STEP_PERCENT):
                set_fan_percent(chip, fan_percent)
                print_step_result(fan_percent, STEP_DELAY_SECONDS)

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        if tach_callback is not None:
            tach_callback.cancel()
        lgpio.gpio_write(chip, FAN_PWM_GPIO, 0)
        lgpio.gpiochip_close(chip)


if __name__ == "__main__":
    main()
