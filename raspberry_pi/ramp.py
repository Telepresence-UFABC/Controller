from requests import post
from datetime import datetime
from time import time_ns
from json import load, dumps
from Adafruit_ADS1x15 import ADS1115
from controller import *

VOLTAGE_READ_PIN = 0
START = time_ns()
start_time = str(datetime.now())
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Run new test every RESET_INTERVAL nanoseconds
RESET_INTERVAL = 3_300_000_000
# ADC gain set to GAIN
GAIN = 1
# Tolerance set to TOLERANCE
TOLERANCE = 0.5
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 5 / 300

# Load controller constants
with open("../system_parameters/controller_1.info", "r") as file:
    consts: dict = load(file)
    C1, C2, C3 = consts["c1"], consts["c2"], consts["c3"]

err = Measure()
u = Measure()

ref = 0
output = 0
curr = time_ns()
prev = 0
prev_reset = 0
normal_operation = 1

adc = ADS1115()


def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


def control(err: Measure, u: Measure) -> float:
    return C1 * u.prev + C2 * err.curr + C3 * err.prev


if __name__ == "__main__":
    rpi = setup()
    while True:
        curr = time_ns()
        if curr - prev >= SAMPLING_INTERVAL:
            output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT
            time = (curr - START) / 1e9

            ref = (curr-prev_reset) / 1e9

            # Update previous and current values
            err.prev = err.curr

            # ref - output if in normal operation, otherwise reference is set to 0
            err.curr = ref * normal_operation - output
            u.prev = u.curr
            u.curr = control(err, u)

            h_bridge_write(rpi, PIN_ONE, PIN_TWO, u.curr)
            data = {"start_time": start_time, "Tempo": time, "Saída": output, "Erro": err.curr, "Esforço": u.curr}
            try:
                post("http://192.168.0.100:8080/log", dumps(data))
            except:
                print("Server is not accessible")
            prev = time_ns()
        if curr - prev_reset >= RESET_INTERVAL:
            normal_operation = 0
            if abs(output) <= TOLERANCE and curr - prev_reset >= 1.5*RESET_INTERVAL:
                normal_operation = 1
                prev_reset = time_ns()