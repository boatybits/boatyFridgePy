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
sleep_ms(1000)

def loadLCD():
    try:
        lcd = I2cLcd(mySensors.i2c, DEFAULT_I2C_ADDR, 4, 20)
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("LCD loaded")
        print('LCD loaded')
    except Exception as e:
        print('Call LCD error =',e)
        
        pass


try:
    print("Init sensors lib")
    mySensors = boatymon.sensors()
    print("Init finished, loading LCD")
    loadLCD()
    print("init loop")
    loop = asyncio.get_event_loop()
    print(mySensors)
    print(mySensors.config["lcdEnabled"])
except Exception as e:
    print('create sensors object error =',e)
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
 #           message = message + "Upper Limit = " + str(mySensors.upperLimit) + "\n"
 #           message = message + "Lower Limit Limit = " + str(mySensors.lowerLimit) + "\n" + "check"
            client.publish("ESP_LOG", message)
            print(message)
            
client.set_callback(mqtt_sub_cb)
    


async def call_sensors():
    while True:
        try:
            mySensors.flashLed()       
            mySensors.getTemp()
            mySensors.getCurrent()
#             mySensors.checkWifi()

#             lcd.move_to(0, 0)
#             lcd.putstr("D%=" + mySensors.data["duty"] + "%")
#             lcd.move_to(0, 1)
#             lcd.putstr("V=" + mySensors.data["voltage"] + "V  ")        
#             lcd.move_to(0, 2)
#             lcd.putstr("Ambient Temp =" + mySensors.data["fridgeAmbient"] + "Deg C")
#             lcd.move_to(0, 3)
#             lcd.putstr("Bitcoin Price =$Huge")
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
