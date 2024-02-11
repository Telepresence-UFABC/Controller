from datetime import datetime as dt
from time import time_ns, sleep
from json import load, dumps
import board, busio, adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

VOLTAGE_READ_PIN = 1
START = time_ns()
id = f"ramp {dt.now().strftime('%Y-%m-%d %H_%M_%S')}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Stop for STOP_INTERVAL nanoseconds after reset
STOP_INTERVAL = 1_000_000_000
# Max value of ramp in nanovolts is set to MAX_RAMP
MAX_RAMP = 2_500_000_000
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

ref = 0
output = 0
curr = time_ns()
prev = 0
prev_ramp = time_ns()
normal_operation = 1

i2c = busio.I2C(board.SCL, board.SDA)

adc = ADS.ADS1115(i2c)


def analog_read(pin: int = 0) -> float:
    return AnalogIn(adc, pin).voltage


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
                    err.pop()
                    err.insert(0, -output)

                    u.pop()
                    u.insert(
                        0,
                        control(TILT_INPUT_COEFS, TILT_OUTPUT_COEFS, err, u),
                    )

                    # negative feedback if normal operation, else move system to 0 position
                    h_bridge_write(
                        rpi,
                        PIN_THREE,
                        PIN_FOUR,
                        ref - output if normal_operation else u[0],
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
                    and abs(1 - output) <= TOLERANCE
                    and curr - prev_ramp >= MAX_RAMP + STOP_INTERVAL
                ):
                    normal_operation = 1
                    prev_ramp = time_ns()
    except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
        print(f"Could not connect to server, error: {e}")
        sleep(2)
