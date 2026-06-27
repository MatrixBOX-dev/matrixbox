from __main__ import display, matrix
import displayio, microcontroller
import os, time, json, functions, ampule, ipaddress, binascii, dicts
#from microcontroller import watchdog
#from watchdog import WatchDogMode
# ----------------------------------------------------------------------------------------
#watchdog.timeout = 60
#watchdog.mode = WatchDogMode.RESET
def wd(): pass
deviations_list = []
deviations_timer = time.monotonic()
ad_timer = time.monotonic()
ad_delay = 10
deviations_delay = 1
button_delay = 15000
delay = 0.05
traindata = {}
no_of_screens_flag = 2
timer = ""
temperature_timer = False
temperature_threshold = 89
currenttime = ""
_currenttime = ""
screen_selector = "1"
today = ""
newstation = ""
scrollsum = " "
ap_name = ""
results = ""
city = "Stockholm"
html_cache = ""
datadict = {}
netlist = []
checknet = 0
version_msg = ""
updatedelay = 20
network_delay = 5
active_message = 0
socket_timeout = 50
reset_timer = 0
exit = False
ping_list = []
ping = 0
port = 80
dns = False
currentfont = 0
saving_state = False
settingstoml = dicts.settingstoml
settingstxt = dicts.settingstxt
fonts = [dicts.font_large, dicts.font_small]
html_decode = dicts.html_decode
station_names_dict = dicts.station_names_dict
first_start = True
on_off_counter = 1
new_version_available = 0
new_ver = 0
starttime = time.monotonic()
uptime = ""
show_station_timer = time.monotonic()
show_station_interval = 400
cpver = 8
settings = {}

version = None
for file in os.listdir():
    print(file[0])
    if file[0] == "v":
        with open(file) as f:
            try: 
                version_file = json.loads(f.read())
                version = str(file[1:])
            except: continue

print(20*"\n")
print("                                            █▀▀▀▀▀▀▀▀▀▀█     T-Skylt")
print("                                            █  ██████  █     av Alex")
print("                                            █    ██    █     och Parham")
print("                                            █    ██    █     ----------")
print("                                            █    ██    █")
print("                                            █▄▄▄▄▄▄▄▄▄▄█     2023-2024")
print("                                            Version: " + str(version))
print()
print("--------------------------------------------------------- ")
print("Checking SETTINGS.TXT:")
try:
    with open("settings.txt") as f:
        settings = json.loads(f.read())
except:
    try:
        with open("settings.txt", "w") as f:
            f.write(json.dumps(settingstxt))
        print("Created new settings file!")
    except: print("Read only!!!")

for all in settingstxt:
    try:settings[all]
    except: settings[all] = settingstxt[all]#; print("Added: " + str(all) + " ---> " + settings[all])

try:
    if_long = display.width
    if_tall = display.height
    rotated = display.rotation in (90, 270)
except:
    if_long = matrix.width
    if_tall = matrix.height
    rotated = False

if "DevKit" in os.uname().machine or os.uname().machine == "Waveshare ESP32-S3-Zero with ESP32S3":
    cpver = 9

print("--------------------------------------------------------- ")
print(" CHIP:           ", os.uname().machine)
print(" VERSION:        ", cpver)
print(" FREQUENCY:      ", microcontroller.cpu.frequency)
print(" SCREEN-WIDTH:   ", if_long)
print("--------------------------------------------------------- ")

#display.rotation = int(settings["rotation"])
group = displayio.Group()
display.root_group = group
display.refresh()
try: display.root_group.hidden = True
except: pass
top = displayio.Bitmap(max(280, if_long), 16, 10)
bottom = displayio.Bitmap(1280, 16, 10)
topbottom = displayio.Bitmap(max(200, if_long, if_tall), max(if_long, if_tall), 10)
palette = displayio.Palette(10, dither=False)


shared = {"loop_counter":-5,          
          "showstation":0,
          "scroll_timer":time.monotonic()-updatedelay,
          "nightcount": 0,
          "startup":1}

cached_departure_data = {}
use_cached_data = False

traffic_dict = {"METRO":settings["METRO"],
                "BUS":settings["BUS"],
                "TRAIN":settings["TRAIN"],
                "TRAM":settings["TRAM"],
                "SHIP":settings["SHIP"]}

 

    


print(settings["stations"]["1"]["mystation"])
if settings["stations"]["1"]["mystation"] == "":
    print("Adding old data to new dict...")
    settings["stations"]["1"]["mystation"] = settings["mystation"]
    settings["stations"]["1"]["siteid"] = settings["siteid"]
    settings["stations"]["1"]["METRO"] = settings["METRO"]
    settings["stations"]["1"]["SHIP"] = settings["SHIP"]
    settings["stations"]["1"]["BUS"] = settings["BUS"]
    settings["stations"]["1"]["TRAIN"] = settings["TRAIN"]
    settings["stations"]["1"]["TRAM"] = settings["TRAM"]
    settings["stations"]["1"]["direction"] = settings["direction"] 
    settings["stations"]["1"]["show_msgs"] = settings["show_msgs"] 
    settings["stations"]["1"]["buses_option"] = settings["buses_option"] 
    settings["stations"]["1"]["red"] = settings["red"] 
    settings["stations"]["1"]["green"] = settings["green"] 
    settings["stations"]["1"]["blue"] = settings["blue"] 
    settings["stations"]["1"]["operator"] = settings["operator"] 
    settings["stations"]["1"]["country"] = settings["country"] 
    settings["stations"]["1"]["offset"] = settings["offset"] 
    print("Done.")
