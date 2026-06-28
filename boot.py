import sys, wifi, socketpool, ampule, time, os, json, microcontroller, storage
import load_settings
import digitalio, board
settings =  load_settings.settings()

s2 = True if "S2Mini with ESP32S2-S2FN4R2" in os.uname().machine else False

if not s2: from load_screen import *
import check_button
from check_button import *
# from check_button import check_if_button_pressed

def boot_splash():
    if not s2: pprint("Booting...", line=0, color="red")

def check_if_button_pressed_on_boot():
    try:
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            result = check_if_button_pressed()
            if result:
                return result
        return 0
    except Exception as e: 
        print(e)
        return 1

def lock():
    storage.disable_usb_drive()
    storage.remount("/", False)
        
boot_splash()


if "unlock" in os.listdir():
    lock()
    try: os.remove("unlock")
    except: pass
    storage.enable_usb_drive()
    if not s2: pprint("Unlocking filesystem")

elif check_if_button_pressed_on_boot():
    if not s2: pprint("Unlocking filesystem")
else:
    lock()
    if not s2: pprint("Locked filesystem")
    time.sleep(1)

try: os.remove("code.py")
except: pass
try: os.remove("reboot_required")
except: pass


try: clearscreen(True)
except Exception as e: 
    if not s2: pprint(str(e))

    
