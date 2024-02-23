from datetime import datetime as dt
from time import time_ns, sleep
from json import load, dumps
import board, busio, adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

VOLTAGE_READ_PIN = 0
N_ITER = 5
id = f"controlled_step {dt.now().strftime('%Y-%m-%d %H_%M_%S')}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5 * 1e6
# Reset after TEST_TIME nanoseconds
TEST_TIME = 3 * 1e9
# Stop for STOP_INTERVAL nanoseconds after reset
STOP_INTERVAL = 1 * 1e9
# ADC gain set to GAIN
GAIN = 1
# Tolerance set to TOLERANCE
TOLERANCE = 0.5
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
VOLT2ANGLE = 300 / 5

# Load controller constants
with open("../system_parameters/controller_pan.info", "r") as file:
    consts: dict = load(file)
    PAN_OUTPUT_COEFS = consts["output"]
    PAN_INPUT_COEFS = consts["input"]

with open(
    "../mini_server/public/server_setup/setup.json",
    "r",
) as file:
    SETUP: dict = load(file)
    SERVER_IP: str = SETUP["SERVER_IP"]

err = len(PAN_INPUT_COEFS) * [0]
u = (len(PAN_OUTPUT_COEFS) + 1) * [0]
output = 5

refs = [0.5 + 0.25 * inc for inc in range(15)]
prev = 0
current_operation = Operation.NORMAL

i2c = busio.I2C(board.SCL, board.SDA)

adc = ADS.ADS1115(i2c)

rpi = setup()


def analog_read(pin: int = 0) -> float:
    return AnalogIn(adc, pin).voltage


# Move to zero position to start testing
while abs(output) > TOLERANCE:
    curr = time_ns()
    if curr - prev < SAMPLING_INTERVAL:
        continue

    output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT

    # Update previous and current values
    err.pop()
    err.insert(0, -output)

    u.pop()
    u.insert(
        0,
        control(PAN_INPUT_COEFS, PAN_OUTPUT_COEFS, err, u),
    )

    h_bridge_write(rpi, PIN_ONE, PIN_TWO, u[0])
    prev = time_ns()

sleep(1)

while True:
    try:
        with connect(f"ws://{SERVER_IP}:3000") as websocket:
            for ref in refs:
                for i in range(N_ITER):
                    prev_reset = time_ns()
                    while True:
                        curr = time_ns()
                        if curr - prev < SAMPLING_INTERVAL:
                            continue

                        output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT

                        # Update previous and current values
                        err.pop()
                        err.insert(
                            0, ref * (current_operation == Operation.NORMAL) - output
                        )

                        u.pop()
                        u.insert(
                            0,
                            control(PAN_INPUT_COEFS, PAN_OUTPUT_COEFS, err, u),
                        )

                        # reference if normal operation, else move system to 0 position
                        h_bridge_write(rpi, PIN_ONE, PIN_TWO, u[0])

                        if current_operation == Operation.NORMAL:
                            time = (curr - prev_reset - STOP_INTERVAL * (i > 0)) / 1e9
                            websocket.send(
                                dumps(
                                    {
                                        "type": "log",
                                        "data": {
                                            "id": f"{ref * VOLT2ANGLE}_deg_{i+1}_{id}",
                                            "Tempo": time,
                                            "Saída": output * VOLT2ANGLE,
                                            "Erro": err[0] * VOLT2ANGLE,
                                            "Esforço": u[0],
                                        },
                                    }
                                )
                            )

                        print(
                            f"Current Operation mode: {current_operation}\n"
                            f"Reference: {ref*VOLT2ANGLE}\n"
                            f"Output: {output*VOLT2ANGLE}\n"
                            f"Error: {err[0]*VOLT2ANGLE}\n"
                            f"Effort: {u[0]}\n\n\n"
                        )

                        prev = time_ns()

                        if (
                            curr - prev_reset - STOP_INTERVAL * (i > 0)
                        ) <= TEST_TIME and current_operation == Operation.NORMAL:
                            continue

                        if current_operation == Operation.NORMAL:
                            current_operation = Operation.RESETTING

                        if (
                            abs(output) <= TOLERANCE
                            and current_operation == Operation.RESETTING
                        ):
                            prev_reset = time_ns()
                            current_operation = Operation.WAITING

                        if (
                            curr - prev_reset >= STOP_INTERVAL
                            and current_operation == Operation.WAITING
                        ):
                            current_operation = Operation.NORMAL
                            break

    except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
        print(f"Could not connect to server, error: {e}")
        sleep(2)
