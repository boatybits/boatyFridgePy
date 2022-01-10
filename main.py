#!/usr/bin/env python3

import machine
from machine import PWM
import esp32
import boatymon
import utime
import uasyncio as asyncio
import uos
from umqtt.simple import MQTTClient
import ubinascii

from time import sleep_ms, ticks_ms 
from machine import I2C, Pin 
from i2c_lcd import I2cLcd             # https://techtotinker.blogspot.com/2021/01/008-micropython-technotes-16x2-lcd.html

DEFAULT_I2C_ADDR = 0x27
machine.freq(80000000)
# i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000) 
sleep_ms(10000)

try:
    loop = asyncio.get_event_loop() 
    mySensors = boatymon.sensors()
    print(mySensors)
except Exception as e:
    print('create sensors objecy error =',e)
    pass

try:
    lcd = I2cLcd(mySensors.i2c, DEFAULT_I2C_ADDR, 4, 20)
    lcd.clear()
except Exception as e:
    print('Call LCD error =',e)
    pass
    
client_id = ubinascii.hexlify(machine.unique_id())
client = MQTTClient(client_id, '10.10.10.1')

def mqtt_sub_cb(topic, msg):
    msgDecoded = msg.decode("utf-8")
    topicDecoded = topic.decode("utf-8")
    print("\n","topic=", topic,"msg=", msg, "Decoded=", msgDecoded, "\n")
    
    if topicDecoded == "inhibit":
        if msgDecoded == "false":
            mySensors.inhibit = False
        elif msgDecoded == "true":
            mySensors.inhibit = True
        elif msgDecoded == "print":
            print("mySensor.inhibit = ", mySensors.inhibit)
            mess = "Inhibit = " + str(mySensors.inhibit)
            client.publish("ESP_LOG",mess)
    if topicDecoded == 'fromPiToEsp':
        if msgDecoded == "config":
            message = ""
            for key, value in mySensors.config.items():
                message = message + key + ":" + str(value) + "\n"
            message = message + "Upper Limit = " + str(mySensors.upperLimit) + "\n"
            message = message + "Lower Limit Limit = " + str(mySensors.lowerLimit) + "\n" + "check"
            client.publish("ESP_LOG", message)
            print(message)
            
client.set_callback(mqtt_sub_cb)
    
# try:
#     client.connect()
#     client.subscribe('fromPiToEsp')
#     client.subscribe('inhibit')
#     utime.sleep(0.25)
#     client.publish("ESP_LOG","client connected and subscribed, MQTT callback set")
#     print('       client connected and subscribed, MQTT callback set')
# except Exception as e:
#     print("mqtt connect error",e)
#     pass

async def call_sensors():
    while True:
        try:
            mySensors.flashLed()       
            mySensors.getTemp()
            mySensors.getCurrent()
#             mySensors.getPressure()
            mySensors.checkWifi()
#             mySensors.getVoltage()
#             print("active = ", mySensors.sta_if.active())
            lcd.move_to(0, 0)
            lcd.putstr("D%=" + mySensors.data["duty"] + "%")
#             print(mySensors.data["duty"])
        except Exception as e:
            print('Call Sensors routine error =',e)
            pass
#         try:    
#             client.check_msg()    
#         except Exception as e:
#             print('MQTT error =',e)
#             pass
        await asyncio.sleep(1)

# async def fast_loop():
#     sreader = asyncio.StreamReader(uart)
#     while True:
#         try:
#             res = await sreader.readline()
#             res = res.decode("ASCII").rstrip()        
#             values = res.split("\t")
#             if values[0] == 'V':                   
#                 voltage = float(int(values[1])/1000)
#                 mySensors.insertIntoSigKdata("batteries.shunt.voltage", voltage)
#             elif values[0] == 'I':                   
#                 current = float(int(values[1])/1000)
#                 mySensors.insertIntoSigKdata("batteries.shunt.current", current)
#             elif values[0] == 'SOC':                   
#                 SOC = float(int(values[1])/10)
#                 mySensors.insertIntoSigKdata("batteries.shunt.soc", SOC)
#             elif values[0] == 'T':                   
#                 T = float(int(values[1])+273.15)
#                 mySensors.insertIntoSigKdata("batteries.shunt.temperature", T)
#         except Exception as e:
#             #print("Serial input decode error",e)
#             pass

loop.create_task(call_sensors())
# loop.create_task(fast_loop())

loop.run_forever()
