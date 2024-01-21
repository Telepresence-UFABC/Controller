from requests import post
from datetime import datetime
from time import time_ns
from json import load, dumps
from Adafruit_ADS1x15 import ADS1115
from controller import *

VOLTAGE_READ_PIN = 0
START = time_ns()
id = f"controlled_step_{str(datetime.now())}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Run new test every RESET_INTERVAL nanoseconds
RESET_INTERVAL = 2_000_000_000
# Stop for STOP_INTERVAL nanoseconds after reset
STOP_INTERVAL = 2_000_000_000
# ADC gain set to GAIN
GAIN = 1
# Tolerance set to TOLERANCE
TOLERANCE = 0.5
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 300 / 5

# Load controller constants
with open("../system_parameters/controller_1.info", "r") as file:
    consts: dict = load(file)
    C1, C2, C3 = consts["c1"], consts["c2"], consts["c3"]

err = Measure()
u = Measure()
output = Measure()

ref = 1.5
curr = time_ns()
prev = 0
prev_reset = time_ns()
normal_operation = 1


adc = ADS1115()


def send_log(data) -> None:
    for entry in data:
        try:
            post("http://192.168.0.100:8080/log", dumps(entry))
        except:
            print("Server is not accessible")
            continue


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
            output.prev = output.curr
            output.curr = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT

            # Update previous and current values
            err.prev = err.curr
            err.curr = ref*normal_operation - output.curr

            u.prev = u.curr
            u.curr = control(err, u)

            # reference if normal operation, else move system to 0 position
            h_bridge_write(rpi, PIN_ONE, PIN_TWO, u.curr)
            data = {
                "id": id,
                "Tempo": (curr-prev_reset)/ 1e9,
                "Saída": output.curr,
                "Erro": err.curr,
                "Esforço": u.curr,
            }

            try:
                post("http://192.168.0.100:8080/log", dumps(data))
            except:
                print("Could not send logs to server")

            prev = time_ns()

        # if RESET_INTERVAL nanoseconds have passed since previous reset
        # exit normal operation
        if curr - prev_reset >= RESET_INTERVAL:
            normal_operation = 0

            # if motor is close to 0 position and at least STOP_INTERVAL nanoseconds
            # have elapsed since reset
            # return to normal operation
            if (
                abs(output.curr) <= TOLERANCE
                and curr - prev_reset >= RESET_INTERVAL + STOP_INTERVAL
            ):
                normal_operation = 1
                prev_reset = time_ns()
