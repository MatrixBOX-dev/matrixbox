import sys, wifi, socketpool, time, os, json, microcontroller, storage

import digitalio, board
try: import ampule
except: pass
try:
    import load_settings
    settings =  load_settings.settings()
except: pass



if not "S2" in os.uname().machine:  # Träskylt:
    try:
        from load_screen import *
        import check_button
        from check_button import *
        # from check_button import check_if_button_pressed
    except:
        def pprint(text, line=0,color=0):
            return
        def time_button(): return
else:
    def pprint(text, line=0,color=0): return
    def time_button(): return

def boot_splash():
    pprint("Booting...", line=0, color="white")

def check_if_button_pressed_on_boot():
    try:
        return time_button()
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
    pprint("Unlocking filesystem",  line=1, color="red")
    time.sleep(1)

elif check_if_button_pressed_on_boot():
    pprint("Unlocking filesystem",  line=1, color="red")
    time.sleep(1)
else:
    lock()
    pprint("Hold to unlock",  line=1, color="green")
    #pprint("Locked filesystem")
    time.sleep(1)

try: os.remove("code.py")
except: pass
try: os.remove("reboot_required")
except: pass


#try: clearscreen(True)
#except Exception as e: pprint(str(e))
#while True: pass
