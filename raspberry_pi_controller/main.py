from time import time_ns
from json import load, loads
from websockets.sync.client import connect, ClientConnection
from raspberry_pi_controller.controller import *

START = time_ns()
SERVER = "ws://192.168.0.100:3000"
# Run new iteration every SAMPLING_INTERVAL nanoseconds
SAMPLING_INTERVAL = 5_000_000
# Run new test every RESET_INTERVAL nanoseconds
RESET_INTERVAL = 2_000_000_000
# Update reference every RECEIVE_INTERVAL nanoseconds
RECEIVE_INTERVAL = 5_000_000

TOLERANCE = 5

# Load ontroller constants
with open("../system_parameters/controller_1.info", "r") as file:
    consts: dict = load(file)
    C1, C2, C3 = consts["c1"], consts["c2"], consts["c3"]

err = Measure()
u = Measure()

ref_pan = 0
curr = time_ns()
prev = 0
prev_reset = 0
prev_receive = 0
normal_operation = 1


def analog_read(rpi: pi, pin: int = 0) -> float:
    return 0


def control(err: Measure, u: Measure) -> float:
    return angle2voltage(C1 * u.prev + C2 * err.curr + C3 * err.prev, V_OUT)


def listen(websocket: ClientConnection) -> float:
    data = websocket.recv(timeout=0)
    pan: float = 0
    if data:
        parsed_data: dict[str, float] = loads(data)
        pan = parsed_data["pan"]
    return pan


if __name__ == "__main__":
    rpi = setup()
    print("Tempo,Saída,Erro,Esforço")
    with connect(SERVER) as websocket:
        while True:
            curr = time_ns()
            if curr - prev >= SAMPLING_INTERVAL:
                output = voltage2angle(analog_read(rpi))
                time = (START - curr) / 1e9

                # Update previous and current values
                err.prev = err.curr

                # ref - output if in normal operation, otherwise reference is set to 0
                err.curr = ref_pan * normal_operation - output
                u.prev = u.curr
                u.curr = control(err, u)

                h_bridge_write(rpi, PIN_ONE, PIN_TWO, u.curr)

                print("%.6f,%.6f,%.6f,%.6f" % (time, output, err.curr, u.curr))
                prev = time_ns()

            if curr - prev_receive >= RECEIVE_INTERVAL:
                ref_pan = listen()
                prev_receive = time_ns()

            if curr - prev_reset >= RESET_INTERVAL:
                normal_operation = 0
                if (
                    abs(output) <= TOLERANCE
                    and curr - prev_reset >= 1.5 * RESET_INTERVAL
                ):
                    normal_operation = 1
                    prev_reset = time_ns()
