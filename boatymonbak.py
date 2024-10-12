import socket
from config import *
from machine import Pin, I2C
import machine
import ujson
import utime
import network
from ina219 import INA219       
from logging import INFO        #required by ina219 SS
import onewire, ds18x20

class sensors:

    __led = Pin(2, Pin.OUT)      #internal led is on pin 2
    p4 = machine.Pin(4)
    __pwm4 = machine.PWM(p4)
    __pwm4.freq(5000)
    __pwm4.duty(0)
    
    data = {"duty" : "0",
            "ambient" : "0",
            "plate" : "0",
            "comp" : "0",
            "voltage" : "0",
            "current" : "0"
        }
    
    check_wifi_counter = 0
    wifi_connect_isRunning = False
#     sta_if = network.WLAN(network.STA_IF)
    current_sensors = {}
    onewirePin = machine.Pin(18)
    wire = onewire.OneWire(onewirePin)


# #___________________________________________________________________________________________
#////////////////// INIT /// /////////////////////////
    def __init__(self):
        print("Running sensors init. Loading Config")
        self.config = config
        self.sta_if = network.WLAN(network.STA_IF)
        print("config loaded, running connect wifi")
        self.connectWifi()
        self.inhibit=False
        self.i2cActive = True
        self.check_wifi_counter = 0
        self.load_i2c()
        self.load_INA()
        self.load_ds18b20()
        self.dbp('new sensors instance created, off we go')
        self.dutyCycle = [0] * 7200
        self.upperLimit = 8
        self.lowerLimit = 6
#         print(self.dutyCycle[0])
 
    def dbp(self, message):
        if config["debugPrint"]:
            print(message)

    def connectWifi(self):
        import network                        #self.sta_if = network.WLAN(network.STA_IF)
        mynet = network.WLAN(network.STA_IF)
        print(mynet.ifconfig()[0])
        if not mynet.isconnected():
            mynet.active(True)
            mynet.ifconfig((config["IP_Address"], '255.255.255.0', '10.10.10.1', '10.10.10.1'))
            mynet.connect(config["ssid"], config["password"])
            ip = mynet.ifconfig()[0]
            print(ip)
            return ip
    


#     def connectWifi(self):
#         self.wifi_connect_isRunning = True
#         self.sta_if.active(True)
# 
#         try:
#             x = self.sta_if.scan()
#             if x is None:
#                 self.wifi_connect_isRunning = False
#                 return
#             print("\n\nwifi networks found - ", x)
#         except Exception as e:
#             print('Error scanning wifi, error =',e)
#             self.wifi_connect_isRunning = False
#             return
#         if not self.sta_if.isconnected():
#             self.dbp('\n\n*****connecting to network...')            
#             try:
#                 self.sta_if.ifconfig((config["IP_Address"], '255.255.255.0', '10.10.10.1', '10.10.10.1'))
#                 self.sta_if.connect(config["ssid"], config["password"])
#             except Exception as e:
#                 message = ('connectWifi() failure, error =',e); self.dbp(message)
#                 pass               
#             counter = 0
#             while not self.sta_if.isconnected():
#                 utime.sleep(0.5)
#                 print("\r>", counter, end = '')      #print counter in same place each iteration
#                 counter += 1
#                 self.flashLed()               
#                 if counter > 20:
#                     self.sta_if.active(False)
#                     self.sta_if.active(True)
# #                     machine.reset()
#                     self.wifi_connect_isRunning = False
#                     return
#                 pass
#         message = ('****CONNECTED!! network config:', self.sta_if.ifconfig()); self.dbp(message)
#         self.wifi_connect_isRunning = False

    def load_i2c(self):
        self.i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000) 
        self.dbp('Scanning i2c bus...')
        devices = self.i2c.scan()
        if len(devices) == 0:
            self.dbp("No i2c devices !")
            self.i2cActive = False
            pass
        else:
            message = '\n\nNo. of i2c devices found:',len(devices); self.dbp(message)
            for device in devices:  
                message = ("Decimal address: ",device," | Hexa address: ",hex(device)); self.dbp(message)
                
    def load_INA(self):
        if not self.i2cActive:
            return
        for i in config["ina"]:            
            if config["ina"][i]["enabled"]:
                try:
                    SHUNT_OHMS = 0.03     #config["ina"][ina]["shunt_Ohms"]
                    self.current_sensors[i] = INA219(SHUNT_OHMS, self.i2c)
                    message = '****INA219 instance created', i,  self.current_sensors[i]; self.dbp(message)
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
                print(self.ds)
                self.roms = self.ds.scan()
                print("ds18 roms =  ", self.roms)
                if self.roms ==[]:
                    self.inhibit=True
                    return
                for rom in self.roms:          
                    print('      DS18b20  devices:', int.from_bytes(rom, 'little'), rom, hex(int.from_bytes(rom, 'little')))
                print('DS18B20 started')
                self.inhibit=False
            except Exception as e:
                self.inhibit=True
                self.__pwm4.duty(0)
                print('ds18b20 start failed, possibly not connected. Error=',e)

    def getCurrent(self):
        if not self.i2cActive:
            return
        for key in self.current_sensors:
            if config["ina"][key]["enabled"]:
                try:
                    self.insertIntoSigKdata("esp.inaf.current", self.current_sensors[key].current()/1000)
                    self.insertIntoSigKdata("esp.inaf.voltage", self.current_sensors[key].voltage())
                    self.insertIntoSigKdata("esp.inaf.inputVoltage", self.current_sensors[key].supply_voltage())
                    self.insertIntoSigKdata("esp.inaf.power", self.current_sensors[key].power())
                    v = int(self.current_sensors[key].supply_voltage()*100)/100
                    
                    self.data["voltage"] = str(v)
                    
                except Exception as e:
                    message = "getCurrent error -", e; self.dbp(message)


 
    def getTemp(self):
        print("Temperature inhibit variable = ", self.inhibit)
        if self.inhibit:
            print("Temperature inhibit active")
            return           
        try:
            self.roms = self.ds.scan()
            self.ds.convert_temp()
            utime.sleep_ms(750)
            for rom in (self.roms):
                for key, value in config["ds18b20"]["devices"].items():
                    if rom == value:
                        temperature = self.ds.read_temp(rom)
                        print("Fridge", key, temperature)
                        #temperature = 9
                        #print("Fridge", key, temperature)
                        self.insertIntoSigKdata(key, temperature + 273.15)
                        if key == "fridge.ambient.temperature" and temperature > self.upperLimit and self.inhibit==False:
                            self.__pwm4.duty(512)
                        elif key == "fridge.ambient.temperature" and temperature < self.lowerLimit:
                            self.__pwm4.duty(0)
                        if self.inhibit==True:
                            self.__pwm4.duty(0)
                        if key == "fridge.ambient.temperature":
                            self.data["fridgeAmbient"] = str(temperature)
                            
            if self.__pwm4.duty() > 1:
                fridgeRunning = 1
                del self.dutyCycle[7199]
                self.dutyCycle.insert(0,1)          
            elif self.__pwm4.duty() == 0:
                fridgeRunning = 0
                del self.dutyCycle[7199]
                self.dutyCycle.insert(0,0)
            self.insertIntoSigKdata("fridge.compresser.running", fridgeRunning)
            total = sum(self.dutyCycle)
            duty = int(total/7200*100)            
            self.insertIntoSigKdata("fridge.dutycycle", duty)
            strDuty = "{:.0d}".format(duty)
            if duty < 10:
                strDuty = "0" + strDuty
            self.data["duty"] =  strDuty          
        except Exception as e:
            print("DS18B20 error Error=",e)
            pass

    def flashLed(self):
        self.__led.value(not self.__led.value())

    def checkWifi(self):
#         print("running check wifi, counter = ", self.check_wifi_counter, "connected = ", self.sta_if.isconnected(),self.sta_if.ifconfig() )

        if not self.sta_if.isconnected() and self.check_wifi_counter>6 and self.wifi_connect_isRunning == False:
            print("Not connected to wifi, running check wifi if loop")
            self.sta_if.active(True)
            x = self.sta_if.scan()
            if not x:
                print("no wifi networks found")
                if self.check_wifi_counter>6:
                    self.check_wifi_counter = 0
                print("restarting")
                machine.reset()
                return        
            for networks in x:
                print(x)
                if networks[0] == b'openplotter':
                    exists = True
                else:
                    exists = False
            if not exists:
                return         
            for i in range(1,10):
                self.flashLed()
                utime.sleep(0.25)
            self.check_wifi_counter = 0
            print("  calling self.connect_wifi")
            self.connectWifi()
            return
        self.check_wifi_counter += 1
        if self.check_wifi_counter>7:
            self.check_wifi_counter = 0        
        return

    def insertIntoSigKdata(self, path, value):
#         https://wiki.python.org/moin/UdpCommunication
        try:
            UDP_IP = "10.10.10.1"
            UDP_PORT = 10119
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _sigKdata = {"updates": [{"values":[]}]}
            _sigKdata["updates"][0]["values"].append( {"path":path,"value": value})
            MESSAGE = (ujson.dumps(_sigKdata))
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
            sock.close()
        except Exception as e:
            print("Send signalk error = ",e)
