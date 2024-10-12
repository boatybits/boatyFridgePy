#!/usr/bin/env python3

import machine
import esp32
import boatymon
import utime
import uasyncio as asyncio
import uos
from umqtt.simple import MQTTClient
import ubinascii
from machine import UART
from i2c_lcd import I2cLcd             # https://techtotinker.blogspot.com/2021/01/008-micropython-technotes-16x2-lcd.html
import urequests


# uart = UART(1, tx=12, rx=14, timeout=50)
# uart.init(baudrate=19200,bits=8,parity=None)
# machine.UART(uart_num, tx=pin, rx=pin, stop=1, invert=UART.INV_TX | UART.INV_RX)

loop = asyncio.get_event_loop() 
mySensors = boatymon.sensors()


DEFAULT_I2C_ADDR = 0x27
#machine.freq(80000000)
# i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000) 
utime.sleep(0.1)

lcd = I2cLcd(mySensors.i2c, DEFAULT_I2C_ADDR, 4, 20)

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def loadLCD(text, row, col):
    try:  
        #lcd.clear()
        lcd.move_to(row, col)
        lcd.putstr(text)
        #print('LCD loaded')
    except Exception as e:
        print('Call LCD error =',e)       
        pass
loadLCD("loaded", 0, 0)

i = 0 
async def call_sensors():

   
    while True:
        try:
            print("running call sensors routine")
            mySensors.check_wifi()
            mySensors.flashLed()       
            mySensors.getTemp()
            #mySensors.getCurrent()
            #lcd.clear()
            message = mySensors.ambientTemp + "C "
            
#             loadLCD(message, 0, 1)
            message = "{:<10}".format(message)
#             url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/environment/wind/speedTrue/value"
#             response = urequests.get(url) #returns a string
#             checkFloat = is_float(response.text)
# #             print(checkFloat)
#             if not checkFloat:
#                 message = message + "offline"
#                 print("message when offline = ", message)
#             else:
#                 value = round(float(response.text)*1.94384, 1)
#                 message = message + str(value) + "KTS"
#             message = "{:<20}".format(message)
            loadLCD(message, 0, 0)
            pass
        except Exception as e:
            print('Call Sensors routine error first =',e)
            pass
        
        # try:
#             url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/forfridge"
#             response = urequests.get(url)
#             print(response.text)
            # url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/electrical/batteries/shunt/current/value/"
            # response = urequests.get(url)
            # value = round(float(response.text), 1)
            # message = str(value) + "A"
            # message = "{:<10}".format(message)
#             url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/environment/wind/directionTrueText/value/"
#             response = urequests.get(url)
#             value = str(response.text)
#             message = message + value
            # message = "{:<20}".format(message)
# #             print("mess (0,1) =", message)
            # loadLCD(message, 0, 1)
# #             
            # url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/electrical/batteries/shunt/capacity/stateOfCharge/value/"
            # response = urequests.get(url)
            # value = round(float(response.text)*100, 1)
            # message = str(value) + "%   "
            # message = "{:<10}".format(message)
#             url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/navigation/speedOverGround/value"
#             response = urequests.get(url)
#             value = round((float(response.text))*1.92, 1)
#             message = message + str(value) + "Kts"
            # message = "{:<20}".format(message)
# #             print("mess (0,2) =", message)
            # loadLCD(message, 0, 2)
# #             
#             url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/environment/outside/temperature/value"
#             response = urequests.get(url)
#             value = float(response.text) - 273.15
#             message = str(value) + "C   "
#             message = "{:<10}".format(message)
            # url = "http://10.42.0.1:3000/signalk/v1/api/vessels/urn:mrn:imo:mmsi:235090919/electrical/batteries/shunt/voltage/value"
            # response = urequests.get(url)
# #             print("requests = ", response.text)
#             if response.text=="":
#                 print("cog returned = null")
            # value = round((float(response.text)), 3)
            # message = message + str(value) + "V"
            # message = "{:<20}".format(message)
            # loadLCD(message, 0, 3)
        # except Exception as e:
        #     print('Call Sensors routine 2nd error =',e)
        #     pass
#         try:    
#             client.check_msg()
#         except Exception as e:
#             print('MQTT error =',e)
#             pass
        await asyncio.sleep(1)



loop.create_task(call_sensors())


loop.run_forever()

