from datetime import datetime as dt
from time import time_ns, sleep
from json import load, loads, dumps
from Adafruit_ADS1x15 import ADS1115
from threading import Thread
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from controller import *

PAN_READ_PIN = 0
TILT_READ_PIN = 1

START = time_ns()
id = f"main {dt.now().strftime('%Y-%m-%d %H_%M_%S')}"
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
    C1_PAN, C2_PAN, C3_PAN = consts["c1"], consts["c2"], consts["c3"]

with open("../system_parameters/controller_1.info", "r") as file:
    consts: dict = load(file)
    C1_TILT, C2_TILT, C3_TILT = consts["c1"], consts["c2"], consts["c3"]

with open(
    "../mini_server/public/server_setup/setup.json",
    "r",
) as file:
    SETUP: dict = load(file)
    SERVER_IP: str = SETUP["SERVER_IP"]

err_pan = Measure()
u_pan = Measure()

err_tilt = Measure()
u_tilt = Measure()

pan = 1.5
tilt = 1.5
curr = time_ns()
prev = 0

adc = ADS1115()


def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))


def control(err: Measure, u: Measure, c1: float, c2: float, c3: float) -> float:
    return c1 * u.prev + c2 * err.curr + c3 * err.prev


def listen() -> None:
    global pan, tilt
    while True:
        try:
            with connect(f"ws://{SERVER_IP}:3000") as websocket:
                websocket.send(dumps({"type": "messages", "messages": ["pose"]}))
                while True:
                    message = loads(websocket.recv())
                    pan = max(0, min(5, message["pan"] * ANGLE_CONSTANT))
                    tilt = max(0, min(5, message["tilt"] * ANGLE_CONSTANT))
        except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
            print(f"Could not connect to server, error: {e}")
            sleep(2)


def main():
    global C1, C2, C3, err_pan, u_pan, err_tilt, u_tilt, pan, tilt, curr, prev, adc
    while True:
        try:
            with connect(f"ws://{SERVER_IP}:3000") as websocket:
                rpi = setup()
                while True:
                    curr = time_ns()
                    if curr - prev >= SAMPLING_INTERVAL:
                        time = (curr - START) / 1e9

                        # Panoramic motor
                        output_pan = analog_read(PAN_READ_PIN) * VOLTAGE_CONSTANT

                        # Update previous and current values
                        err_pan.prev = err_pan.curr
                        err_pan.curr = pan - output_pan

                        u_pan.prev = u_pan.curr
                        u_pan.curr = control(err_pan, u_pan, C1_PAN, C2_PAN, C3_PAN)

                        h_bridge_write(rpi, PIN_ONE, PIN_TWO, u_pan.curr)


                        # Tilt motor
                        output_tilt = analog_read(TILT_READ_PIN) * VOLTAGE_CONSTANT

                        # Update previous and current values
                        err_tilt.prev = err_tilt.curr
                        err_tilt.curr = tilt - output_tilt

                        u_tilt.prev = u_tilt.curr
                        u_tilt.curr = control(err_tilt, u_tilt, C1_TILT, C2_TILT, C3_TILT)

                        h_bridge_write(rpi, PIN_THREE, PIN_FOUR, u_tilt.curr)


                        websocket.send(
                            dumps(
                                {
                                    "type": "log",
                                    "data": {
                                        "id": id,
                                        "Tempo": time,
                                        "Saída Pan": output_pan,
                                        "Erro Pan": err_pan.curr,
                                        "Esforço Pan": u_pan.curr,
                                        "Saída Tilt": output_tilt,
                                        "Erro Tilt": err_tilt.curr,
                                        "Esforço Tilt": u_tilt.curr,
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
