
import sys, wifi, socketpool, time, os, json, microcontroller, ampule, gc
import load_settings
import digitalio, board
import adafruit_connection_manager, adafruit_requests
settings =  load_settings.settings()
from load_screen import *
from check_button import *

if "apps" in os.listdir():
    for file in os.listdir("apps"):
        try: os.rename("apps/" + file, file)
        except: pass
    try: os.rmdir("apps")
    except: pass

def show_logo():
    pprint("MatrixBOX(", line=0, color="yellow", hr="¨", _refresh=False, overlay=True)
    #pprint("", line=0, color="brightwhite", overlay=True)
    pprint("Matrix", line=0, color="brightwhite", overlay=True)

_anim_x = display.width+1
def logo_anim_step():
    global _anim_x
    W = display.width
    if _anim_x >= W:
        #_anim_x = 0
        return
    x = _anim_x
    saved = []
    for y in (2, 4):
        old = window[x, y]
        saved.append(old)
        if old == 7:
            window[x, y] = 9
        elif old == 5:
            window[x, y] = 2
        elif old == 2:
            window[x, y] = 5
        elif old == 1:
            window[x, y] = 2
    refresh()
    for i, y in enumerate((2, 4)):
        window[x, y] = saved[i]
    _anim_x += 1
    if _anim_x >= W:
        refresh()

show_logo()

wifi.radio.tx_power = 9.0
pool = socketpool.SocketPool(wifi.radio)
socket = pool.socket()
socket.setblocking(False)
socket.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
socket.bind(('', 80))
socket.listen(5)
socket_timeout = 5
macid = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] # mac-id för hotspot
wifi_status = ""
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
first_start = True
screensaver = time.monotonic()

def start_hotspot():
    try:
        wifi.radio.start_ap(ssid=macid)
        #wifi.radio.start_dhcp_ap() # Removed (maybe causing connection error http://None )
        pprint("Started WIFI: ")
        pprint(str(macid))
        pprint(str(wifi.radio.ipv4_address_ap))
    except Exception as e: pprint(str(e))

def connect_to_network(timeout=False, silent=False):
    global wifi_status
    wifi_status = ""
    print("Connecting...")
    try: 
        if not silent: pprint(str(settings["ssid"]))
        channel = settings.get("channel", 0)
        if channel:
            wifi.radio.connect(str(settings["ssid"]), str(settings["password"]), channel=int(channel), timeout=timeout)
        else:
            wifi.radio.connect(str(settings["ssid"]), str(settings["password"]), timeout=timeout)
        pprint(str(wifi.radio.ipv4_address))
        savesettings(settings)
    except Exception as e: 
        if not silent: 
            if "unknown failure" in str(e).lower(): e = "Router distance!"
            if "no network with" in str(e).lower(): e = "Wrong WIFI name"
            if "authentication failure" in str(e).lower(): e = "Wrong password"
            print(e)
            pprint(str(e), color="red")
        wifi_status = str(e)
        print(e)
    return time.monotonic()

@ampule.route("/exit", method="GET")
def webinterface(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/", method="GET")
def webinterface(request):
    global _anim_x
    _anim_x = 0
    if load_settings.app_running: 
        return (200, {}, str(exitbutton) + f"""<br> running app {load_settings.app_running}""")
    if request.params:
        if "run" in request.params: load_settings.app_running = request.params["run"]
    return (200, {}, select_app())

def initialize_app():
    global autostart
    ampule_routes_backup = ampule.routes.copy()
    palette_backup = [palette[i] for i in range(12)]  # restored on exit

    try:
        clearscreen(lines=True)
        pprint(f"Starting {load_settings.app_running}...")
        os.chdir(load_settings.app_running)
        time.sleep(0.5)
        ampule.routes.clear()  # apps start with a clean route table
        import __init__
    except Exception as e:
        print(f"{e}")
        settings["autostart"] = 0
    finally:
        for i, backup in enumerate(palette_backup):
            palette[i] = backup
        try: microcontroller.cpu.frequency = 160000000
        except: pass
        autostart = False
        ampule.routes = ampule_routes_backup.copy()
        try:
            for codefile in os.listdir():
                try: del sys.modules[codefile.rsplit(".", 1)[0]]
                except: pass
        except: pass
        gc.collect()  # reclaim the exited app's bitmaps so the next launch is clean
        display.root_group = rf_group
        os.chdir("/")
        clearscreen(lines=True)  # zero the window so a buggy app leaves no artifacts
        show_logo()
        _wifi_address = f"IP: {wifi.radio.ipv4_address}" if wifi.radio.ipv4_address else "OFFLINE"
        pprint(_wifi_address, line=1)
        pprint("Select app:", line=2)
        show_first_app()
        return False

def savesettings(settings):
    print("Saving...")
    clearscreen(True)
    try:
        with open("settings.txt","w") as f:
            f.write(json.dumps(settings))
    except:
         print("Read only!")
    clearscreen(False)

def installed_apps():
    installed_apps = []
    for app in os.listdir("/"):
        if app == "LICENSE": continue
        if not "." in app:
            try:
                if not "__init__.py" in os.listdir("/" + app): continue
            except: continue
            installed_apps.append(app)
    return installed_apps if len(installed_apps) else ["No apps found"]

def show_first_app():
    try: load_settings.installed_apps_list[1]
    except: load_settings.installed_apps_list = installed_apps()
    pprint(load_settings.installed_apps_list[0], line=-1, color="yellow", clear=True, _refresh=True)

def next_program_in_list(run=False):
    try: load_settings.installed_apps_list[1]
    except: load_settings.installed_apps_list = installed_apps()
    if run:
        load_settings.app_running = load_settings.installed_apps_list[0]
        return
    print(load_settings.installed_apps_list)
    load_settings.installed_apps_list.append(load_settings.installed_apps_list[0])
    load_settings.installed_apps_list.pop(0)
    scroll_line(load_settings.installed_apps_list[0], color="yellow")

def check_for_button_next_program():
    global screensaver
    b = check_if_button_pressed()
    if b == 0: pass
    if b == 1: next_program_in_list()
    elif b == 2: next_program_in_list(run=True)
    if load_settings.app_running: 
        load_settings.app_running = initialize_app()
        screensaver = time.monotonic()

autostart = settings["autostart"]
screensaver_app = settings.get("screensaver", "starcloud")
wifi.radio.tx_power = float(settings["wifi_power"])

from web_interface import *
connect_to_network()
#first_start = False

while 1:
    print("Entered main loop")
    while not wifi.radio.connected and not wifi.radio.ap_active:
        check_network_again_timer = time.monotonic()
        start_hotspot()
    
    while wifi.radio.ap_active and not wifi.radio.connected: 
        ampule.listen(socket)
        if autostart:
            print(ampule.listen(socket))
            load_settings.app_running = autostart
        check_for_button_next_program()
        if time.monotonic() > check_network_again_timer + 10:
            print("Attempting... " + str(wifi.radio.tx_power))
            wifi.radio.tx_power += 1
            if wifi.radio.tx_power == 21: wifi.radio.tx_power = 18
            check_network_again_timer = connect_to_network(timeout=3, silent=True)
        if first_start == False and wifi.radio.connected: wifi.radio.stop_ap()
        
    while wifi.radio.connected or wifi.radio.ap_active:
        settings["wifi_power"] = wifi.radio.tx_power
        pprint("Select app:")
        show_first_app()
        while wifi.radio.connected:# or wifi.radio.ap_active:
            first_start = False
            if autostart:
                print(ampule.listen(socket))
                load_settings.app_running = autostart
            elif not load_settings.app_running: ampule.listen(socket)
            check_for_button_next_program()
            logo_anim_step()

            if screensaver_app and time.monotonic() > screensaver + 60:
                try: load_settings.app_running = screensaver_app
                except Exception as e: pprint(e)
                screensaver = time.monotonic()

            
            
            
