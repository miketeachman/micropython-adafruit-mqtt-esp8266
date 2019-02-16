# The MIT License (MIT)
# Copyright (c) 2018 Mike Teachman
# https://opensource.org/licenses/MIT
#
# Example MicroPython and CircuitPython code showing how to use the MQTT protocol with Adafruit IO, to  
# publish and subscribe on the same device
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
import gc
import sys
from machine import Pin,ADC,PWM

#pin = Pin(2, Pin.OUT, value = 1)
adc = ADC(0)
pwm = PWM(Pin(2))

def cb_03(topic, msg):	
	pwm.duty(int(msg))

# WiFi connection information
WIFI_SSID = 'LG'
WIFI_PASSWORD = 'lg123456'

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
ADAFRUIT_USERNAME = b'icreate'
ADAFRUIT_IO_KEY = b'697847b8dfbb4b43b8f06bf7ed037887'
#ADAFRUIT_IO_FEEDNAME_01 = b'freeHeap'
ADAFRUIT_IO_FEEDNAME_02 = b'ambient-light'
ADAFRUIT_IO_FEEDNAME_03 = b'onboard-led'

client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=ADAFRUIT_USERNAME, 
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
                    
try:            
    client.connect()
except Exception as e:
    print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
    sys.exit()

# publish free heap statistics to Adafruit IO using MQTT
# subscribe to the same feed
#
# format of feed name:  
#   "ADAFRUIT_USERNAME/feeds/ADAFRUIT_IO_FEEDNAME"
#mqtt_feedname_01 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME_01), 'utf-8')
mqtt_feedname_02 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME_02), 'utf-8')
mqtt_feedname_03 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME_03), 'utf-8')

#client.set_callback(cb_01)
#client.set_callback(cb_02)
client.set_callback(cb_03)

#client.subscribe(mqtt_feedname_01)
#client.subscribe(mqtt_feedname_02)
client.subscribe(mqtt_feedname_03)
  
PUBLISH_PERIOD_IN_SEC = 3 
SUBSCRIBE_CHECK_PERIOD_IN_SEC = 0.5 
accum_time = 0

while True:
    
    try:
        # Publish
        if accum_time >= PUBLISH_PERIOD_IN_SEC:
            free_heap_in_bytes = gc.mem_free()
            print('Publish:  rawPot = {}'.format(adc.read()))
            client.publish(mqtt_feedname_02,    
                           bytes(str(adc.read()), 'utf-8'), 
                           qos=0)
			#client.publish(mqtt_feedname_03, f(y))    
            #               bytes(str(free_heap_in_bytes), 'utf-8'), 
            #               qos=0)
            accum_time = 0                
        

        # Subscribe.  Non-blocking check for a new message.  
        client.check_msg()

        time.sleep(SUBSCRIBE_CHECK_PERIOD_IN_SEC)
        accum_time += SUBSCRIBE_CHECK_PERIOD_IN_SEC
    
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        client.disconnect()
        sys.exit()
