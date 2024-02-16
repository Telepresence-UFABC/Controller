import cv2, time, base64
import board, busio, adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from datetime import datetime as dt
from time import time_ns, sleep
from json import load, loads, dumps
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
with open("../system_parameters/controller_pan.info", "r") as file:
    consts: dict = load(file)
    PAN_OUTPUT_COEFS = consts["output"]
    PAN_INPUT_COEFS = consts["input"]

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
    RPI_WIDTH: int = SETUP["RPI_WIDTH"]
    RPI_HEIGHT: int = SETUP["RPI_HEIGHT"]

err_pan = len(PAN_INPUT_COEFS) * [0]
u_pan = (len(PAN_OUTPUT_COEFS) + 1) * [0]

err_tilt = len(TILT_INPUT_COEFS) * [0]
u_tilt = (len(TILT_OUTPUT_COEFS) + 1) * [0]

pan = 1.5
tilt = 1.5
curr = time_ns()
prev = 0

i2c = busio.I2C(board.SCL, board.SDA)

adc = ADS.ADS1115(i2c)


def analog_read(pin: int = 0) -> float:
    return AnalogIn(adc, pin).voltage


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


def send_video() -> None:
    while True:
        try:
            with connect(f"ws://{SERVER_IP}:3000") as websocket:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, RPI_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RPI_HEIGHT)
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    ok, video_buffer = cv2.imencode(".jpg", frame)
                    frame = base64.b64encode(video_buffer).decode("utf-8")
                    websocket.send(dumps({"type": "remote_video", "media": frame}))

        except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
            print(f"Could not connect to server, error: {e}")
            time.sleep(2)


def main() -> None:
    global err_pan, u_pan, err_tilt, u_tilt, pan, tilt, curr, prev
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
                        err_pan.pop()
                        err_pan.insert(0, pan - output_pan)

                        u_pan.pop()
                        u_pan.insert(
                            0,
                            control(PAN_INPUT_COEFS, PAN_OUTPUT_COEFS, err_pan, u_pan),
                        )

                        h_bridge_write(rpi, PIN_ONE, PIN_TWO, u_pan[0])

                        # Tilt motor
                        output_tilt = analog_read(TILT_READ_PIN) * VOLTAGE_CONSTANT

                        # Update previous and current values
                        err_pan.pop()
                        err_pan.insert(0, tilt - output_tilt)

                        u_tilt.pop()
                        u_tilt.insert(
                            0,
                            control(
                                TILT_INPUT_COEFS, TILT_OUTPUT_COEFS, err_tilt, u_tilt
                            ),
                        )

                        h_bridge_write(rpi, PIN_THREE, PIN_FOUR, u_tilt[0])
                        
                        data = {
                                    "type": "log",
                                    "data": {
                                        "id": id,
                                        "Tempo": time,
                                        "Saída Pan": output_pan / ANGLE_CONSTANT,
                                        "Erro Pan": err_pan[0] / ANGLE_CONSTANT,
                                        "Esforço Pan": u_pan[0],
                                        "Saída Tilt": output_tilt / ANGLE_CONSTANT,
                                        "Erro Tilt": err_tilt[0] / ANGLE_CONSTANT,
                                        "Esforço Tilt": u_tilt[0],
                                    },
                                }
                        websocket.send(dumps(data))

                        print(f"Pan: {output_pan / ANGLE_CONSTANT}, Esforco Pan: {u_pan[0]}, Erro Pan: {err_pan[0] / ANGLE_CONSTANT}\nTilt: {output_tilt / ANGLE_CONSTANT}, Esforco Tilt: {u_tilt[0]}, Erro Tilt: {err_tilt[0] / ANGLE_CONSTANT}")

                        prev = time_ns()
        except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
            print(f"Could not connect to server, error: {e}")
            sleep(2)


listen_thread = Thread(target=listen)
listen_thread.start()

main_thread = Thread(target=main)
main_thread.start()

send_video_thread = Thread(target=send_video)
send_video_thread.start()
