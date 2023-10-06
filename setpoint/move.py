import pigpio as pio, requests
from json import loads

pi = pio.pi()
PAN_PIN = 17
MAX_ANGLE = 90

def _map(x, in_low, in_high, out_low, out_high):
    return (x-in_low)*(out_high-out_low)/(in_high-in_low)+out_low

def get_pulsewidth_from_angle(angle: int) -> int:
    if angle > MAX_ANGLE:
        angle = MAX_ANGLE
    elif angle < -MAX_ANGLE:
        angle = -MAX_ANGLE
    return int(1000 * angle / MAX_ANGLE + 1500)


def move_servo(angle: int) -> None:
    angle_pulsewidth = get_pulsewidth_from_angle(angle)
    pi.set_servo_pulsewidth(PAN_PIN, angle_pulsewidth)

while True:
    resp = requests.get("http://localhost:8080/coord").json()
    angle = _map(resp[0], 0, 640, -90, 90)
    move_servo(angle)