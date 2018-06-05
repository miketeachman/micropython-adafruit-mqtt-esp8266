# The MIT License (MIT)
# Copyright (c) 2018 Mike Teachman
# https://opensource.org/licenses/MIT
#
# Example MicroPython and CircuitPython code showing how to use the MQTT protocol to  
# subscribe to an Adafruit IO feed
#
# Tested using the releases:
#   ESP8266
#       MicroPython 1.9.3
#       MicroPython 1.9.4
#       CircuitPython 2.3.1     (needs addition of CircuitPython specific umqtt module)
#       CircuitPython 3.0.0     (needs addition of CircuitPython specific umqtt module)
#   ESP32
#       MicroPython 1.9.4       (needs addition of MicroPython umqtt module)
#
# Tested using the following boards:
#   Adafruit Feather HUZZAH ESP8266
#   Adafruit Feather HUZZAH ESP32
#   WeMos D1 Mini
#
# User configuration parameters are indicated with "ENTER_".  

import network
import time
from umqtt.robust import MQTTClient
import os
import sys

# the following function is the callback which is 
# called when subscribed data is received
def cb(topic, msg):
    print('Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    free_heap = int(str(msg,'utf-8'))
    print('free heap size = {} bytes'.format(free_heap))

# WiFi connection information
WIFI_SSID = '<ENTER_WIFI_SSID>'
WIFI_PASSWORD = '<ENTER_WIFI_PASSWORD>'

# turn off the WiFi Access Point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# connect the device device to the WiFi network
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

# wait until the device is connected to the WiFi network
MAX_ATTEMPTS = 20
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:
    attempt_count += 1
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()

# create a random MQTT clientID 
random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')

# connect to Adafruit IO MQTT broker using unsecure TCP (port 1883)
# 
# To use a secure connection (encrypted) with TLS: 
#   set MQTTClient initializer parameter to "ssl=True"
#   Caveat: a secure connection uses about 9k bytes of the heap
#         (about 1/4 of the micropython heap on the ESP8266 platform)
ADAFRUIT_IO_URL = b'io.adafruit.com' 
ADAFRUIT_USERNAME = b'<ENTER_ADAFRUIT_USERNAME>'
ADAFRUIT_IO_KEY = b'<ENTER_ADAFRUIT_IO_KEY>'
ADAFRUIT_IO_FEEDNAME = b'freeHeap'

client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=ADAFRUIT_USERNAME, 
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
  
client.set_callback(cb)                    
  
try:      
    client.connect()
except Exception as e:
    print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
    sys.exit()

mqtt_feedname = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME), 'utf-8')    
client.subscribe(mqtt_feedname)  

# wait until new data has been Published to the Adafruit IO feed
while True:
    try:
        client.wait_msg()
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        sys.exit()