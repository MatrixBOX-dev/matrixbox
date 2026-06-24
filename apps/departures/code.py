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
#################################
try:
    if wifi.radio.connected == True:
        with open("/settings.txt") as f:
            data = json.loads(f.read())
            for line in data:
                if line == "ssid": varinit.settings["ssid"] = data["ssid"]
                if line == "password": varinit.settings["password"] = data["password"]
except Exception as e:
    print("Error loading underlying WIFI settings:", e)
#################################
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
        # Dest TileGrid smooth scroll (runs every main-loop iteration in listmode)
        if int(varinit.settings["listmode"]) and int(varinit.settings.get("dest_scroll", 0)):
            try:
                _nt = time.monotonic()
                _scrolled = False
                for _rx, _rs in varinit.dest_scroll_state.items():
                    _ov = _rs["overflow"]
                    if _ov <= 0: continue
                    if _nt < _rs.get("pause_end", 0): continue
                    _pos = _rs["pos"]
                    if _pos >= _ov:
                        # End of scroll: reset to start with pause
                        _rs["pos"] = 0
                        _rs["pause_end"] = _nt + 1.5
                        varinit.dest_tgs[_rx].x = _rs["start_x"]
                    else:
                        _rs["pos"] = _pos + 1
                        varinit.dest_tgs[_rx].x = _rs["start_x"] - _pos - 1
                    _scrolled = True
                if _scrolled: refresh()
            except: pass
        
