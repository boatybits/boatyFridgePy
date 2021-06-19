import socket
from config import *
from machine import Pin, I2C
import machine
import ujson
import utime
import network
from ina219 import INA219    
from logging import INFO        #required by ina219 SS
import bme280_float             #https://github.com/robert-hh/BME280
import ads1x15                  #https://github.com/robert-hh/ads1x15
# import usocket

import onewire, ds18x20


class sensors:

    __led = Pin(2, Pin.OUT)      #internal led is on pin 2
    __D4 = Pin(4, Pin.OUT)      
    __D5 = Pin(5, Pin.OUT)
    __D18 = Pin(18, Pin.OUT)
    
    
    check_wifi_counter = 0
    wifi_connect_isRunning = False
    sta_if = network.WLAN(network.STA_IF)
    current_sensors = {}
    onewirePin = machine.Pin(15)
    wire = onewire.OneWire(onewirePin)

# #___________________________________________________________________________________________
#////////////////// INIT /// /////////////////////////
    def __init__(self):
        self.config = config
        
        self.load_i2c()
        self.load_INA()
#         self.load_BME()
        self.load_ds18b20()
#         self.load_ads1115()
        self.dbp('new sensors instance created, off we go')
        self.__D4.value(0)
        self.__D5.value(0)
        self.__D18.value(0)
        self.connectWifi()
 
    def dbp(self, message):
        if config["debugPrint"]:
            print(message)

    def connectWifi(self):
        self.wifi_connect_isRunning = True
        self.sta_if.active(True)
        try:
            x = self.sta_if.scan()
            if x is None:
                self.wifi_connect_isRunning = False
                return
            print("\n\nwifi networks found - ", x)
        except Exception as e:
            print('No networks found, error =',e)
            self.wifi_connect_isRunning = False
            return
        if not self.sta_if.isconnected():
            self.dbp('\n\n*****connecting to network...')            
            try:
                self.sta_if.ifconfig((config["IP_Address"], '255.255.255.0', '192.168.43.78', '192.168.43.78'))
                self.sta_if.connect(config["ssid"], config["password"])
            except Exception as e:
                message = ('connect wifi failure, error =',e); self.dbp(message)
                pass               
            counter = 0
            while not self.sta_if.isconnected():
                utime.sleep(0.25)
                print("\r>", counter, end = '')      #print counter in same place each iteration
                counter += 1
                self.flashLed()               
                if counter > 10:
                    machine.reset()
                    break
                pass
        message = ('****CONNECTED!! network config:', self.sta_if.ifconfig()); self.dbp(message)
        self.wifi_connect_isRunning = False

    def load_i2c(self):
        self.i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000) 
        self.dbp('Scanning i2c bus...')
        devices = self.i2c.scan()
        if len(devices) == 0:
            self.dbp("No i2c device !")
        else:
            message = '\n\nNo. of i2c devices found:',len(devices); self.dbp(message)
            for device in devices:  
                message = ("Decimal address: ",device," | Hexa address: ",hex(device)); self.dbp(message)
                
    def load_INA(self):        
        for i in config["ina"]:            
            if config["ina"][i]["enabled"]:
                try:
                    SHUNT_OHMS = 0.1     #config["ina"][ina]["shunt_Ohms"]
                    self.current_sensors[i] = INA219(SHUNT_OHMS, self.i2c)
                    message = '\n****INA219 instance created', i,  self.current_sensors[i]; self.dbp(message)
                except Exception as e:
                    message = "****INA start error - ", e; self.dbp(message)                
                try:
                    self.current_sensors[i].configure()
#                     self.current_sensors[i].configure(RANGE_16V,GAIN_1_40MV,ADC_12BIT,ADC_12BIT)        # gain defaults to 3.2A. ina219.py line 132
                    message = '\n****INA219 instance configure run with ', self.current_sensors[i]; self.dbp(message)
                except Exception as e:
                    message = 'INA configure failed, possibly not connected. Error=',e;  self.dbp(message)
   
  

    def load_ds18b20(self):
        if config["ds18b20"]["enabled"]:
            try:
                self.ds = ds18x20.DS18X20(self.wire)
                self.roms = self.ds.scan()
                if self.roms ==[]:
                    self.roms = 0
                for rom in self.roms:          
                    print('      DS18b20  devices:', int.from_bytes(rom, 'little'), rom, hex(int.from_bytes(rom, 'little')))
                print('DS18B20 started')
            except Exception as e:
                print('ds18b20 start failed, possibly not connected. Error=',e)

    def getCurrent(self):
        for key in self.current_sensors:
            if config["ina"][key]["enabled"]:
                try:
                    self.insertIntoSigKdata("esp.inaf.current", self.current_sensors[key].current()*1.6)
                    self.insertIntoSigKdata("esp.inaf.voltage", self.current_sensors[key].voltage())
                    self.insertIntoSigKdata("esp.inaf.inputVoltage", self.current_sensors[key].supply_voltage())
                    self.insertIntoSigKdata("esp.inaf.power", self.current_sensors[key].power())
#                     v = self.current_sensors[key].voltage()
#                     a = self.current_sensors[key].current()
#                     self.dbp(v)
#                     self.dbp(a)
                except Exception as e:
                    message = "getCurrent error -", e; self.dbp(message)


 
    def getTemp(self):
        try:
            self.roms = self.ds.scan()
            self.ds.convert_temp()
            utime.sleep_ms(200)
            for rom in (self.roms):
                for key, value in config["ds18b20"]["devices"].items():
                    if rom == value:
                        temperature = self.ds.read_temp(rom)
                        self.insertIntoSigKdata(key, temperature + 273.15)
                        if key == "fridge.ambient.temperature" and temperature > 6:
                            self.__D5.value(1)
                        elif key == "fridge.ambient.temperature" and temperature < 4:
                            self.__D5.value(0)
            if self.__D4.value()==1 or self.__D5.value()==1 or self.__D18.value()==1:
                dutyCycle = 1
            elif self.__D4.value()==0 and self.__D5.value()==0 and self.__D18.value()==0:
                dutyCycle = 0
            self.insertIntoSigKdata("fridge.compresser.running", dutyCycle)
                            
                            
#             print(self.ds.read_temp(rom))                             
        except Exception as e:
            print("DS18B20 error Error=",e)
            pass
    

    def flashLed(self):
        self.__led.value(not self.__led.value())
#         self.__D18.value(not self.__D18.value())

    def checkWifi(self):
        if not self.sta_if.isconnected() and self.check_wifi_counter>6 and self.wifi_connect_isRunning == False:
            for i in range(1,10):
                self.flashLed()
                utime.sleep(0.25)
            self.check_wifi_counter = 0
            self.connectWifi()
            return
        self.check_wifi_counter += 1
        return

    def insertIntoSigKdata(self, path, value):
#         https://wiki.python.org/moin/UdpCommunication
        try:
            UDP_IP = "192.168.43.93"
            UDP_PORT = 10119
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _sigKdata = {"updates": [{"values":[]}]}
            _sigKdata["updates"][0]["values"].append( {"path":path,"value": value})
#             _sigKdata["updates"][0]["values"].append( {"path","23"})
#             print(ujson.dumps(_sigKdata))
            MESSAGE = (ujson.dumps(_sigKdata))
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
            sock.close()
        except Exception as e:
            print("Send signalk error = ",e)

#     
