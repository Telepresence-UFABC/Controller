import board, busio, adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from controller import *

PAN_READ_PIN = 0
TILT_READ_PIN = 1
# ADC gain set to GAIN
GAIN = 1
# 3.3 V to 5 V
VOLTAGE_CONSTANT = 5 / 3.3
# 1V every 60 deg
ANGLE_CONSTANT = 300 / 5

i2c = busio.I2C(board.SCL, board.SDA)

adc = ADS.ADS1115(i2c)


def analog_read(pin: int = 0) -> float:
    return AnalogIn(adc, pin).voltage


while True:
    pan = analog_read(PAN_READ_PIN) * VOLTAGE_CONSTANT * ANGLE_CONSTANT
    tilt = analog_read(TILT_READ_PIN) * VOLTAGE_CONSTANT * ANGLE_CONSTANT
    print(f"Pan: {pan}, Tilt: {tilt}")
