from datetime import datetime as dt
from time import time_ns, sleep
from json import load, dumps
from Adafruit_ADS1x15 import ADS1115
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

VOLTAGE_READ_PIN = 1
START = time_ns()
id = f"step_open_loop {dt.now().strftime('%Y-%m-%d %H_%M_%S')}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 30_000_000
# Run new test every RESET_INTERVAL nanoseconds
RESET_INTERVAL = 500_000_000
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
with open("../system_parameters/controller_tilt.info", "r") as file:
    consts: dict = load(file)
    TILT_OUTPUT_COEFS = consts["output"]
    TILT_INPUT_COEFS = consts["input"]

with open(
    "../mini_server/public/server_setup/setup.json",
    "r",
) as file:
    SETUP: dict = load(file)
    SERVER_IP: str = SETUP["SERVER_IP"]

err = len(TILT_INPUT_COEFS) * [0]
u = (len(TILT_OUTPUT_COEFS) + 1) * [0]
output = [0, 0]

ref = 5
curr = time_ns()
prev = 0
prev_reset = time_ns()
normal_operation = 1

adc = ADS1115()


def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


while True:
    try:
        with connect(f"ws://{SERVER_IP}:3000") as websocket:
            rpi = setup()
            while True:
                curr = time_ns()
                if curr - prev >= SAMPLING_INTERVAL:
                    output[1] = output[0]
                    output[0] = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT

                    delta_t = (curr - prev) / 1e9
                    speed = (output[0] - output[1]) * ANGLE_CONSTANT / delta_t

                    time = (curr - prev_reset) / 1e9

                    # Update previous and current values, reference is always set to 0
                    err.pop()
                    err.insert(0, 1 - output)

                    u.pop()
                    u.insert(
                        0,
                        control(TILT_INPUT_COEFS, TILT_OUTPUT_COEFS, err, u),
                    )

                    # reference if normal operation, else move system to 0 position
                    h_bridge_write(
                        rpi, PIN_THREE, PIN_FOUR, ref if normal_operation else u[0]
                    )

                    websocket.send(
                        dumps(
                            {
                                "type": "log",
                                "data": {"id": id, "Tempo": time, "Saída": speed},
                            }
                        )
                    )
                    prev = time_ns()

                # if RESET_INTERVAL nanoseconds have passed since previous reset
                # exit normal operation
                if curr - prev_reset >= RESET_INTERVAL:
                    normal_operation = 0

                    # if motor is close to 0 position and at least STOP_INTERVAL nanoseconds
                    # have elapsed since reset
                    # send logs to server
                    # return to normal operation
                    if (
                        abs(1 - output[0]) <= TOLERANCE
                        and curr - prev_reset >= RESET_INTERVAL + STOP_INTERVAL
                    ):
                        normal_operation = 1
                        prev_reset = time_ns()
    except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
        print(f"Could not connect to server, error: {e}")
        sleep(2)
