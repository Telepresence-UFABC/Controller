from Adafruit_ADS1x15 import ADS1115
from controller import *

PAN_READ_PIN = 0
TILT_READ_PIN = 1
# ADC gain set to GAIN
GAIN = 1
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 300 / 5

adc = ADS1115()

def adc2voltage(val: int) -> float:
    return max(0, val / 32767 * 4.096)


def analog_read(pin: int = 0) -> float:
    return adc2voltage(adc.read_adc(pin, gain=GAIN))

while True:
    pan = analog_read(PAN_READ_PIN) * VOLTAGE_CONSTANT * ANGLE_CONSTANT
    tilt = analog_read(TILT_READ_PIN) * VOLTAGE_CONSTANT * ANGLE_CONSTANT
    print(f"Pan: {pan}, Tilt: {tilt}")