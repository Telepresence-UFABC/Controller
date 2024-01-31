from datetime import datetime as dt
from time import time_ns, sleep
from json import load, dumps
from Adafruit_ADS1x15 import ADS1115
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

VOLTAGE_READ_PIN = 0
START = time_ns()
id = f"ramp {dt.now().strftime('%Y-%m-%d %H_%M_%S')}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Stop for STOP_INTERVAL nanoseconds after reset
STOP_INTERVAL = 2_000_000_000
# Max value of ramp in nanovolts is set to MAX_RAMP
MAX_RAMP = 5_000_000_000
# ADC gain set to GAIN
GAIN = 1
# Tolerance set to TOLERANCE
TOLERANCE = 0.5
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 300 / 5

# Load controller constants
with open("../system_parameters/controller_pan.info", "r") as file:
    consts: dict = load(file)
    C1, C2, C3 = consts["c1"], consts["c2"], consts["c3"]

with open(
    "../mini_server/public/server_setup/setup.json",
    "r",
) as file:
    SETUP: dict = load(file)
    SERVER_IP: str = SETUP["SERVER_IP"]

err = Measure()
u = Measure()

ref = 0
output = 0
curr = time_ns()
prev = 0
prev_ramp = time_ns()
normal_operation = 1

adc = ADS1115()


def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


def control(err: Measure, u: Measure) -> float:
    return C1 * u.prev + C2 * err.curr + C3 * err.prev


while True:
    try:
        with connect(f"ws://{SERVER_IP}:3000") as websocket:
            rpi = setup()
            while True:
                curr = time_ns()
                if curr - prev >= SAMPLING_INTERVAL:
                    output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT

                    time = (curr - START) / 1e9

                    # if ramp has reached max value, reset to 0 position
                    if curr - prev_ramp >= MAX_RAMP:
                        normal_operation = 0

                    # Ramp goes from 0 to MAX_RAMP nanovolts
                    ref = (curr - prev_ramp) / 1e9

                    # Update previous and current values, reference is always set to 0
                    err.prev = err.curr
                    err.curr = -output

                    u.prev = u.curr
                    u.curr = control(err, u)

                    # negative feedback if normal operation, else move system to 0 position
                    h_bridge_write(
                        rpi,
                        PIN_ONE,
                        PIN_TWO,
                        ref - output if normal_operation else u.curr,
                    )
                    websocket.send(
                        dumps(
                            {
                                "type": "log",
                                "data": {
                                    "id": id,
                                    "Tempo": time,
                                    "Referencia": ref * ANGLE_CONSTANT,
                                    "Saída": output * ANGLE_CONSTANT,
                                    "Erro": (ref - output) * ANGLE_CONSTANT,
                                },
                            }
                        )
                    )
                    prev = time_ns()
                # if motor is not in normal operation
                # is close to 0 position
                # and STOP_INTERVAL nanoseconds have passed since reset
                # send logs and restart normal operation
                if (
                    normal_operation == 0
                    and abs(output) <= TOLERANCE
                    and curr - prev_ramp >= MAX_RAMP + STOP_INTERVAL
                ):
                    normal_operation = 1
                    prev_ramp = time_ns()
    except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
        print(f"Could not connect to server, error: {e}")
        sleep(2)
