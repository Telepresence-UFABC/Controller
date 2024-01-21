from pigpio import pi

V_OUT = 5
PIN_ONE = 17
PIN_TWO = 27
PWM_FREQUENCY = 1_000
PWM_MAX_RANGE = 32767


class Measure:
    def __init__(self, prev=0, curr=0):
        self.prev = prev
        self.curr = curr


def setup() -> pi:
    # Setup
    rpi = pi()

    # Set PWM range
    rpi.set_PWM_range(PIN_ONE, PWM_MAX_RANGE)
    rpi.set_PWM_range(PIN_TWO, PWM_MAX_RANGE)

    # Set PWM frequency
    rpi.set_PWM_frequency(PIN_ONE, PWM_FREQUENCY)
    rpi.set_PWM_frequency(PIN_TWO, PWM_FREQUENCY)

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
