import os
from __main__ import *
stop_wifi = True
from functions import *
from check_button import *
varinit.last_button_state = last_button_state
varinit.button = button
varinit.gbutton = gbutton
varinit.debounce_delay = debounce_delay

def check_button():
    b = check_if_button_pressed()
    if b == 1:
        if int(varinit.settings.get("button_mode", 0)):
            varinit.deviations_timer = time.monotonic()
            if varinit.display.width > 64 and varinit.display.height <= 32:
                varinit.settings["listmode"] = 1 - int(varinit.settings["listmode"])
            functions.switch(_screen=True)
        else:
            nightcheck(_switch=True, turnon=varinit.group.hidden); refresh()
    elif b == 2:
        varinit.exit = True
delay = version_delay()
#microcontroller.cpu.frequency = 240000000
from functions import refresh
disp_init()
if varinit.display.width <= 64 or varinit.display.height > 32:
    varinit.settings["listmode"] = 1
scroll_mode()
while not varinit.exit:
    while wifi.radio.connected == False and not varinit.exit:           # CHECK CONNECTION ###################
        try: wifi.radio.stop_ap()
        except: pass
        
        start_ap()
        stop_wifi = False
        if varinit.tg3.y == 32: functions.switch(force=True, wifi_screen=True)
        varinit.reset_timer = time.monotonic()
        while wifi.radio.connected == False and not varinit.exit:
            if time.monotonic() > varinit.reset_timer + varinit.network_delay:
                varinit.reset_timer = time.monotonic()
                wifiattempt(errmsg=False, _timeout=10, skipversion=True)
                update_screen()
            ampule.listen(socket)
    if varinit.settings["listmode"] and not varinit.tg3.y == 0: functions.switch(force=False, _cls=bottom)
    varinit.first_start = False
    if stop_wifi: wifi.radio.stop_ap()
    x = 1
    while wifi.radio.connected == True and not varinit.exit:            # MAINLOOP ###########################
        x = 1 - x
        if x: 
            ampule.listen(socket)
            check_button()
        if int(varinit.settings["listmode"]) and time.monotonic() > varinit.shared["scroll_timer"] + updatedelay: varinit.shared["scroll_timer"] = list_mode()
        elif not int(varinit.settings["listmode"]) and varinit.display.width > 64: 
            varinit.tg2.x -= 1
            refresh(int(delay + varinit.settings["scroll"]) + 1 * (delay*2))
            if varinit.tg2.x < -varinit.scrollsum: scroll_mode()
            elif time.monotonic() > varinit.shared["scroll_timer"] + updatedelay and shared["loop_counter"] >= 0: scroll_mode()
        
