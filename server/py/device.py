import time
try:
    from smbus2 import SMBus
except:
    from smbus import SMBus
from bme280 import BME280

from time import sleep

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

# need to call get_temperature once to allow the sensor to set up correctly
# (compensation data, sampling rate, etc)
# if this is not done, it will return an incorrect temperature reading
bme280.get_temperature()
# wait 100 ms to ensure set up is complete
sleep(0.1)
# can now return correct temperature in F
print(bme280.get_temperature()*9/5+32)
