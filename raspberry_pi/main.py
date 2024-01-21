from datetime import datetime
from time import time_ns, sleep
from json import load, loads, dumps
from Adafruit_ADS1x15 import ADS1115
from threading import Thread
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

VOLTAGE_READ_PIN = 0
START = time_ns()
id = f"main_{str(datetime.now())}"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Receive new reference every RECEIVE_INTERVAL nanoseconds
RECEIVE_INTERVAL = 500_000_000
# ADC gain set to GAIN
GAIN = 1
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 5 / 300

# Load controller constants
with open("../system_parameters/controller_1.info", "r") as file:
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

pan = 1.5
tilt = 0
curr = time_ns()
prev = 0

adc = ADS1115()


def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


def control(err: Measure, u: Measure) -> float:
    return C1 * u.prev + C2 * err.curr + C3 * err.prev


def listen() -> None:
    global pan, tilt
    while True:
        try:
            with connect(f"ws://{SERVER_IP}:3000") as websocket:
                while True:
                    message = loads(websocket.recv())
                    if (
                        message["type"] == "manual_pose"
                        or message["type"] == "auto_pose"
                    ):
                        pan = max(0, min(5, message["pan"] * ANGLE_CONSTANT))
                        tilt = max(0, min(5, message["tilt"] * ANGLE_CONSTANT))
        except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
            print(f"Could not connect to server, error: {e}")
            sleep(2)


def main():
    while True:
        try:
            with connect(f"ws://{SERVER_IP}:3000") as websocket:
                rpi = setup()
                while True:
                    curr = time_ns()
                    if curr - prev >= SAMPLING_INTERVAL:
                        output = analog_read(VOLTAGE_READ_PIN) * VOLTAGE_CONSTANT
                        time = (curr - START) / 1e9

                        # Update previous and current values
                        err.prev = err.curr
                        err.curr = pan - output

                        u.prev = u.curr
                        u.curr = control(err, u)

                        h_bridge_write(rpi, PIN_ONE, PIN_TWO, u.curr)

                        websocket.send(
                            dumps(
                                {
                                    "type": "log",
                                    "data": {
                                        "id": id,
                                        "Tempo": time,
                                        "Saída": output,
                                        "Erro": err.curr,
                                        "Esforço": u.curr,
                                    },
                                }
                            )
                        )

                        prev = time_ns()
        except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
            print(f"Could not connect to server, error: {e}")
            sleep(2)


listen_thread = Thread(target=listen)
listen_thread.start()

main_thread = Thread(target=main)
main_thread.start()
