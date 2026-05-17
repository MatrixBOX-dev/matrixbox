import json
from __main__ import *

def settings(): 
     settings = {"ssid":"T-Skylt WIFI",                                                      # Default settings:
                "password":"dunderskurre",
                "autostart":False,
                "screensaver":0,
                "rotation":0,
                "width":64,
                "height":32,
                "tiles":1,
                "repository_url":"https://raw.githubusercontent.com/MatrixBOX-dev/matrixbox/refs/heads/main/", 
                "repository_file":"repository.txt",
                "wifi_power":20,
                "ai_provider":"",
                "ai_key":"",
                "ai_model":""}
     try: settings["repository_url"] = settings["repository_url"].replace("https://raw.githubusercontent.com/matrixbox", "https://raw.githubusercontent.com/MatrixBOX-dev")
     except: pass
     try: #iteration
            defaults = set(settings)
            with open("settings.txt") as f: settings.update(json.loads(f.read()))
            for key in list(settings):
                if key not in defaults:
                    del settings[key]
            for setting in settings:
                _type = str
                try: 
                     int(settings[setting])
                     _type = int
                except: pass
                settings[setting] = _type(settings[setting])
                
     
     except Exception as e: 
         print("No previous settings!")
         print(e)
     return settings


    

app_running = False
latest_available_apps = []
