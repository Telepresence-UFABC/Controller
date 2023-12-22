from requests import get
from pigpio import pi
from time import time_ns
from json import load
from Adafruit_ADS1x15 import ADS1115

class Measure:
    def __init__(self, prev=0, curr=0):
        self.prev = prev
        self.curr = curr

# System parameters
V_OUT = 5
PWM_FREQUENCY = 1_000
PWM_MAX_RANGE = 255
VOLTAGE_READ_PIN = 0
PIN_ONE = 17
PIN_TWO = 27

START = time_ns()

# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Run new test every RESET_INTERVAL nanoseconds
RESET_INTERVAL = 2_000_000_000
# Receive new reference every RECEIVE_INTERVAL nanoseconds
RECEIVE_INTERVAL = 2_000_000_000
# ADC gain set to GAIN
GAIN = 1
# Tolerance set to TOLERANCE
TOLERANCE = 5
# Enables testing
TESTING = False
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5/3.3
# 1V every 60 deg
ANGLE_CONSTANT = 300/5

# Load controller constants
with open("../system_parameters/controller_1.info", "r") as file:
    consts: dict = load(file)
    C1, C2, C3 = consts["c1"], consts["c2"], consts["c3"]

err = Measure()
u = Measure()

ref_pan = 1.5
curr = time_ns()
prev = 0
prev_reset = 0
prev_receive = 0
normal_operation = 1

adc = ADS1115()

def adc2voltage(val: int) -> float:
    return max(0, val/32767*4.096)

def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


def control(err: Measure, u: Measure) -> float:
    return C1 * u.prev + C2 * err.curr + C3 * err.prev


# Setup
rpi = pi()

# Set PWM range
rpi.set_PWM_range(PIN_ONE, PWM_MAX_RANGE)
rpi.set_PWM_range(PIN_TWO, PWM_MAX_RANGE)

# Set PWM frequency
rpi.set_PWM_frequency(PIN_ONE, PWM_FREQUENCY)
rpi.set_PWM_frequency(PIN_TWO, PWM_FREQUENCY)

if __name__ == "__main__":
    print("Tempo,Saída,Erro,Esforço")
    while True:
        curr = time_ns()
        if curr - prev >= SAMPLING_INTERVAL:
            output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT
            time = (curr - START) / 1e9

            # Update previous and current values
            err.prev = err.curr

            # ref - output if in normal operation, otherwise reference is set to 0
            err.curr = ref_pan * normal_operation - output
            u.prev = u.curr
            u.curr = control(err, u)
            
            # Control
            value = max(-V_OUT, min(V_OUT, u.curr))

            pwm = PWM_MAX_RANGE / V_OUT * abs(value)

            # FORWARD
            if value > 0:
                rpi.set_PWM_dutycycle(PIN_ONE, pwm)
                rpi.set_PWM_dutycycle(PIN_TWO, 0)
            # FORWARD
            elif value < 0:
                rpi.set_PWM_dutycycle(PIN_ONE, 0)
                rpi.set_PWM_dutycycle(PIN_TWO, pwm)
            # BRAKE
            else:
                rpi.set_PWM_dutycycle(PIN_ONE, 0)
                rpi.set_PWM_dutycycle(PIN_TWO, 0)
            
            print("%.6f,%.6f,%.6f,%.6f" % (time, output, err.curr, u.curr))
            prev = time_ns()
        if curr - prev_receive >= RECEIVE_INTERVAL:
            try:
                ref: dict[str, float] = get("192.168.0.100:8080/reference").json()
                ref_pan = max(0, min(5, ref.get("ref_pan", 0)*ANGLE_CONSTANT))
            except:
                pass
            finally:
                prev_receive = time_ns()