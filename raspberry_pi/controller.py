from pigpio import pi

V_OUT = 5
PIN_ONE = 17
PIN_TWO = 27
PIN_THREE = 23
PIN_FOUR = 24
PWM_FREQUENCY = 1_000
PWM_MAX_RANGE = 32767


class Operation:
    NORMAL = 0
    RESETTING = 1
    WAITING = 2


def control(input_coefs: list, output_coefs: list, input: list, output: list) -> float:
    return sum(c[0] * c[1] for c in zip(input_coefs, input)) + sum(
        c[0] * c[1] for c in zip(output_coefs, output)
    )


def setup() -> pi:
    # Setup
    rpi = pi()

    # Set PWM range
    rpi.set_PWM_range(PIN_ONE, PWM_MAX_RANGE)
    rpi.set_PWM_range(PIN_TWO, PWM_MAX_RANGE)
    rpi.set_PWM_range(PIN_THREE, PWM_MAX_RANGE)
    rpi.set_PWM_range(PIN_FOUR, PWM_MAX_RANGE)

    # Set PWM frequency
    rpi.set_PWM_frequency(PIN_ONE, PWM_FREQUENCY)
    rpi.set_PWM_frequency(PIN_TWO, PWM_FREQUENCY)
    rpi.set_PWM_frequency(PIN_THREE, PWM_FREQUENCY)
    rpi.set_PWM_frequency(PIN_FOUR, PWM_FREQUENCY)

    return rpi


def h_bridge_write(rpi: pi, pin_one: int, pin_two: int, value: float) -> None:
    """
    ACT | P1 | P2

    FWD | 1 | 0

    BWD | 0 | 1

    BRK | 0 | 0

    BRK | 1 | 1
    """
    value = max(-V_OUT, min(V_OUT, value))

    pwm = PWM_MAX_RANGE / V_OUT * abs(value)

    # FORWARD
    if value > 0:
        rpi.set_PWM_dutycycle(pin_one, pwm)
        rpi.set_PWM_dutycycle(pin_two, 0)
    # FORWARD
    elif value < 0:
        rpi.set_PWM_dutycycle(pin_one, 0)
        rpi.set_PWM_dutycycle(pin_two, pwm)
    # BRAKE
    else:
        rpi.set_PWM_dutycycle(pin_one, 0)
        rpi.set_PWM_dutycycle(pin_two, 0)
