#
# Micropython ESP8266 code to Publish temperature sensor data to an Adafruit IO Feed using the MQTT protocol
# Also publishes statistics on the number of free bytes on the micropython Heap
#
# Hardware used:
# - Adafruit Huzzah ESP8266 running micropython version esp8266-20160909-v1.8.4.bin
# - Adafruit MCP9808 temperature breakout board
# - USB to serial converter
#

# prerequisites:
# - Adafruit account
# - registered to use Adafruit IO

#
# References and Kudos
#
# Big thanks to Tony DiCola from Adafruit for excellent tutorials on:
#   Ampy tutorial:  valuable tool to efficiently develop python code on ESP8266 hardware:  
#     https://learn.adafruit.com/micropython-basics-load-files-and-run-code
#   i2c on micropython hardware tutorial:  
#     https://learn.adafruit.com/micropython-hardware-i2c-devices
# 

import network
import time
import machine
import gc
from umqtt.simple import MQTTClient

#
# conversion routine, MCP9808 2-byte response --> Degrees C (courtesy of Tony DiCola)
#
def convertMCP9808ToDegC(data):
    value = data[0] << 8 | data[1]
    temp = (value & 0xFFF) / 16.0
    if value & 0x1000:
        temp -= 256.0
    return temp

#
# configure i2c for communication to MCP9808 sensor hardware
#
i2cDeviceAddress = 24
i2cRegisterAddress = 5
i2cNumBytesToRead = 2
i2c = machine.I2C(machine.Pin(5), machine.Pin(4))

#
# connect the ESP8266 to local wifi network
#
yourWifiSSID = "<enter your wifi SSID here>"
yourWifiPassword = "<enter your wifi password here>"
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(yourWifiSSID, yourWifiPassword)
while not sta_if.isconnected():
  pass
  
#
# connect ESP8266 to Adafruit IO using MQTT
#
myMqttClient = "miket-mqtt-client"  # can be anything unique
adafruitIoUrl = "io.adafruit.com" 
adafruitUsername = "<enter your Adafruit Username here>"  # can be found at "My Account" at adafruit.com
adafruitAioKey = "<enter your Adafruit IO Key here>"  # can be found by clicking on "VIEW AIO KEYS" when viewing an Adafruit IO Feed
c = MQTTClient(myMqttClient, adafruitIoUrl, 0, adafruitUsername, adafruitAioKey)
c.connect()

#
# publish temperature and free heap to Adafruit IO using MQTT
#
# note on feed name in the MQTT Publish:  
#    format:
#      "<adafruit-username>/feeds/<adafruitIO-feedname>"
#    example:
#      "MikeTeachman/feeds/feed-TempInDegC"
#
#
while True:
  dataFromMCP9808 = i2c.readfrom_mem(i2cDeviceAddress, i2cRegisterAddress, i2cNumBytesToRead)  # read temperature from sensor using i2c
  tempInDegC = convertMCP9808ToDegC(dataFromMCP9808)
  c.publish("MikeTeachman/feeds/feed-TempInDegC", str(tempInDegC))  # publish temperature to adafruit IO feed
  c.publish("MikeTeachman/feeds/feed-micropythonFreeHeap", str(gc.mem_free()))  #publish num free bytes on the Heap
  time.sleep(5)  # number of seconds between each Publish
  
c.disconnect()  

