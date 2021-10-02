
config = {
    "esp_Name" : "ESP2",
    "ssid" : "openplotter",
    "password" : "12345678",
    "debugPrint" : True,
    "IP_Address" : "10.10.10.162",
    "ina": {
        "ina1" : {
            "enabled" : True,
            "addr" : "ox40",
            "shunt_Ohms" : "0.06"
            },
        "ina2" : {
            "enabled" : False,
            "addr" : "ox44",
            "shunt_Ohms" : "0.1"
            }        
        },
    "bmeEnabled" : True,
    "ds18b20" :  {
            "enabled" : True,
            "devices" : {
                "spare1" : bytearray(b'(\xf77V\x05\x00\x00\xd8'),
                "fridge.compressor.temperature" : bytearray(b'(\xdb\xa1F\x05\x00\x00\x00'),
                "fridge.ambient.temperature" : bytearray(b'(\xa0\xa4V\x05\x00\x00\x8a'),
                "fridge.plate.temperature" : bytearray(b'(\x99\x11V\x05\x00\x00l'),
                "electrical.batteries.housebank.temperature" : bytearray(b'(\xdd\xdfU\x05\x00\x00\xcd')                
                }
        }
    }
