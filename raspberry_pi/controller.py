from pigpio import pi

# System parameters
VCC_RASPBERRY = 3.3
V_OUT = 5
PWM_MAX_RANGE = 1000
PIN_ONE = 17
PIN_TWO = 27


class Measure:
    def __init__(self, prev=0, curr=0):
        self.prev = prev
        self.curr = curr


def setup() -> pi:
    rpi = pi()

    # 0 <= PWM <= PWM_MAX_RANGE
    rpi.set_PWM_range(PIN_ONE, PWM_MAX_RANGE)
    rpi.set_PWM_range(PIN_TWO, PWM_MAX_RANGE)
    
    return rpi


def voltage2angle(voltage: float) -> float:
    """Converts potentiometer measured voltage to angle"""
    # Max angle read by potentiometer is 300°
    return voltage / VCC_RASPBERRY * 300


def angle2voltage(angle: float, v_level: float = VCC_RASPBERRY) -> float:
    """Converts angle to voltage, taking into account the appropriate voltage level"""
    # Max angle read by potentiometer is 300°
    return angle / 300 * v_level


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
