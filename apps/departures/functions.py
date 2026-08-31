from __main__ import wifi, pool
import varinit, createhtml, microcontroller, json, ipaddress
from varinit import *
import random

mac = [hex(i) for i in wifi.radio.mac_address]
id = "".join(mac)
#ap_name = "t-skylt" + id[-2:]; varinit.ap_name = ap_name
ap_name = "matrixbox-" + "".join(mac).replace("0x","")[:3] # mac-id för hotspot


def pwd_gen(): return id.replace("0x","")[:8]
def cls(__screen, _refresh=False):
    __screen.fill(0)
    if _refresh: refresh()
def reset():
    displayio.release_displays()
    microcontroller.reset()
def strlen(_string): 
    if isinstance(_string, str): _string = _string.lower()
    return sum(fonts[varinit.currentfont][c][0] for c in _string)

LOGO_CHAR = "Ⓜ"

def temperature_check():
    if round(microcontroller.cpu.temperature) > varinit.temperature_threshold: 
        print("Temp-warning: ", round(microcontroller.cpu.temperature))
        if not varinit.temperature_timer: varinit.temperature_timer = time.monotonic()
        elif time.monotonic() > varinit.temperature_timer + 60*2: 
            print("Temperature fail! Restarting...")
            import safemode
    else: varinit.temperature_timer = False

def ping_screen():
    while varinit.ping:
        start_time = time.monotonic()
        _data = fetch_data("data.t-skylt.se",90,"/get_departures?country=se&operator=sl&station=9001", )
        end_time = time.monotonic()
        varinit.ping_list.append(int(end_time - start_time))
        print("temp: ", str(round(microcontroller.cpu.temperature)))
        if len(varinit.ping_list) > 5: varinit.ping_list.pop(0)
        sysprint(str(varinit.ping_list), 0, color="red", shading=True, _refresh=True, ontop=True)
    return True

def ad_message():
    varinit.ad_timer = time.monotonic()
    data = fetch_data(host="data.t-skylt.se", port=89, args="/settings?ad")
    ad = json.loads(data)
    return str(ad[1]) if ad[0] else False

def check_button():
    if varinit.last_button_state:
        if not varinit.button.value:
            varinit.time.sleep(varinit.debounce_delay)
            if not varinit.button.value:
                varinit.shared["nightcount"] = 0
                x = 0 
                while not varinit.button.value and x < varinit.button_delay * 2: x+=1
                if x > varinit.button_delay and not varinit.group.hidden:
                    varinit.exit = True
                else:
                    if int(varinit.settings.get("button_mode", 0)):
                        varinit.deviations_timer = time.monotonic()
                        if varinit.display.width > 64 and varinit.display.height <= 32:
                            varinit.settings["listmode"] = 1 - int(varinit.settings["listmode"])
                        switch(_screen=True)
                    else:
                        nightcheck(_switch=True, turnon=varinit.group.hidden); refresh()
    varinit.last_button_state = varinit.button.value

def check_timer():
    try:
        for day in varinit.settings["timer"]:
            if varinit.settings["timer"][day] and day[:3] == varinit.today:
                if compare_time(varinit.settings["timer"][day][0]) == compare_time(varinit.settings["timer"][day][1]): return True
                if compare_time(varinit.settings["timer"][day][0]) < compare_time(varinit._currenttime) < compare_time(varinit.settings["timer"][day][1].replace("00:00","24:00")):
                    print(varinit.settings["timer"][day][0], "<", varinit._currenttime, "<", varinit.settings["timer"][day][1])
                    return True
                else: return False
    except Exception as e:
        print(e)
        return True
    return True

def compare_time(time1):
    return time.struct_time(["","","",time1.split(":")[0],time1.split(":")[1],"","","",""])


def version_delay(slowdown=False):
    try:
        if slowdown:
            if slowdown == 1:
                if varinit.cpver == 9 and varinit.if_long > 128: microcontroller.cpu.frequency = 80000000
            elif slowdown == 2:
                if varinit.cpver == 9 and varinit.if_long > 128: microcontroller.cpu.frequency = 180000000
            return
    except: pass
    wifi.radio.stop_ap()
    wifi.radio.tx_power = 17.0
    #wifi.radio.tx_power = 13.0
    
    varinit.button_delay = 20000 #varinit.debounce_delay = 0.5  
    try: microcontroller.cpu.frequency = 180000000
    except: pass
    return 100

def reset_scroll(_delay=0):
    varinit.deviations_timer = time.monotonic()
    varinit.shared["scroll_timer"] = 0
    time.sleep(_delay)
    if varinit.first_start: return
    varinit.shared["loop_counter"] = 0

def sysprint(_string, line, color=True, cls=False, shading=False, _refresh=True, ontop=False, _delay=0):
    _invertcolor = 2 if shading else 0
    renderstring(_string + " ", line, smallfont=True, sys_msg=color, shading=shading, shade=False, invertcolor=_invertcolor, _cls=cls, ontop=ontop)
    refresh() if _refresh else None
    time.sleep(_delay)

def switch(_screen=True, _cls=False, force=False, wifi_screen=False):
    def bounce(direction):
        for x in range(32):
            varinit.tg1.y -= -direction
            varinit.tg2.y -= -direction
            varinit.tg3.y -= -direction
            refresh()
    if _cls: cls(_cls)
    if _screen: 
        direction = -1 if force and not varinit.tg3.y == 0 or not varinit.tg3.y == 0 else 1
        if direction == -1: 
            cls(topbottom)
            if not force: list_splash(_settings=varinit.shared["startup"])
            if wifi_screen: update_screen()
        else: 
            renderstring(varinit.text[4]+ varinit.settings["stations"]["1"]["mystation"][:16], 1, 0,large=True, _cls=top)
        bounce(direction)
    cls(bottom, _refresh=True)
    reset_scroll()

def load_text():
    
    http = "" if int(varinit.settings["long"]) == -1 else "http://"
    if not varinit.settings["no_more_departures"]: varinit.settings["no_more_departures"] = dicts.language[settings["language"]]["display"]["no_more_departures"]
    _logo = "((" + LOGO_CHAR + " "
    return [_logo+dicts.language[settings["language"]]["display"]["sign"],#+" v" + settings["version"] + "     ",
            "WIFI: " + settings["ssid"] + "      ",
            dicts.language[settings["language"]]["display"]["your_settings"],
            http,
            _logo,
            "",
            varinit.settings["no_more_departures"] + " "*200,
            dicts.language[settings["language"]]["display"]["check_connection"] + ": http://",
            "Besök t-skylt.se för driftstatus",
            dicts.language[settings["language"]]["display"]["_north_south"],
            dicts.language[settings["language"]]["display"]["_north"],
            dicts.language[settings["language"]]["display"]["_south"]]

def colors():
    varinit.group.hidden = False
    factor = int(varinit.settings["brightness"])+1
    if not varinit.settings["color"]: _color = (factor*50,factor*20,0)
    elif varinit.settings["color"] == 1: _color = (factor*40,factor*20,0)
    elif varinit.settings["color"] == 2: _color = (factor*20,factor*20,factor*20)
    varinit.palette[1] = _color
    try: varinit.dest_palette[1] = _color
    except: pass
    try:
        varinit.overlay_palette[1] = _color
        varinit.overlay_palette[2] = varinit.palette[2]
    except: pass

def get_deviations():
    country = varinit.settings["stations"]["1"]["country"]
    operator = varinit.settings["stations"]["1"]["operator"]
    siteid = varinit.settings["stations"]["1"]["siteid"]
    if not len(varinit.deviations_list):
        data = fetch_data(host="data.t-skylt.se", port=90, args="/get_deviations?country=" + country + "&operator=" + operator + "&station=" + siteid)
        data = json.loads(data)
        varinit.deviations_list = data
    print(*varinit.deviations_list, sep='\n')
    return varinit.deviations_list.pop(0)

def convert_date(dt):
    if_gmt = 60 * (60*2) if "GMT" in dt else 0
    print("■ RFC1123: ", dt)
    try: varinit.today = dt.split(",")[0].replace(" ", "")
    except: pass
    for x in dicts.weekday:
        try: dt = dt.split(x)[1][2:]
        except: continue
    _date = dt.split()[0][:2]
    __month = dt.split(_date + " ")[1][:3]
    _month = dicts.month[__month]
    _year = dt.split(__month + " ")[1][:4]
    _hour = dt.split(_year + " ")[1][:2]
    _minute = dt.split(_hour + ":")[1][:2]
    _second = dt.split(_minute + ":")[1][:2]
    
    if not varinit.first_start: varinit._currenttime = (_hour + ":" + _minute)
    _newtime = time.mktime(time.struct_time((int(_year), int(_month), int(_date), int(_hour), int(_minute), int(_second), 0, 0, -1)))
    return _newtime + if_gmt

def manual_dns():
    try:
        print("Attempting manual DNS settings:")
        with open("no_dhcp") as f: no_dhcp = json.loads(f.read())
        for lines in no_dhcp: print(lines, no_dhcp[lines])
        print("---------------------------------------")
        wifi.radio.stop_dhcp()
        new_ip = no_dhcp["ip"]
        new_netmask = no_dhcp["netmask"]
        new_gateway = no_dhcp["gateway"]
        new_dns = no_dhcp["dns"] if len(no_dhcp["dns"]) > 5 else "8.8.8.8"
        wifi.radio.set_ipv4_address(ipv4=ipaddress.IPv4Address(new_ip), netmask=ipaddress.IPv4Address(new_netmask), gateway=ipaddress.IPv4Address(new_gateway), ipv4_dns=ipaddress.IPv4Address(new_dns)) # 
        print("Setting new IP: ", new_ip)
    except: pass

def wifiattempt(errmsg=True, _timeout=None, skipversion=False):
    _timeout = 5
    if "no_dhcp" in os.listdir(): manual_dns()
    #if varinit.settings["ssid"] == "my_ssid": return
    if wifi.radio.connected == True: return
    try:
        wifi.radio.enabled = True
        wifi.radio.connect(ssid=varinit.settings["ssid"], password=varinit.settings["password"].replace("%23","#"), timeout=_timeout)
        print("Connected to ", varinit.settings["ssid"])
        if not varinit.first_start: sysprint(varinit.settings["ssid"], 100, cls=topbottom)
    except Exception as e: 
        print("WIFI fail for " + varinit.settings["ssid"] + ": ", e)
        varinit.network_delay = 20 if "authentication" in str(e).lower() else 5
        if errmsg:
            if not varinit.first_start: sysprint(str(e), 100, _refresh=True, cls=topbottom, _delay=1)

def check_version():
    try: 
        try: 
            ver_txt = json.loads(fetch_data(host="t-skylt.se", port=80, args="/update/ver.txt",filetype="text"))
            varinit.new_ver = ver_txt["ver"]
            print(varinit.new_ver)
        except: print("Failed to download ver.txt")
        
        if float(varinit.new_ver) > float(varinit.settings["version"]): varinit.new_version_available = 1
        else: print("No new version available")
        #try: varinit.dicts.country_and_operators = ver_txt["country_and_operators"]
        #except: print("Failed to append Operators/Countries")
        try: varinit.ad_delay = ver_txt["ad_delay"]
        except: print("Failed to set advertisement-delay, using default: ", varinit.ad_delay)
        try: varinit.temperature_threshold = ver_txt["temperature_threshold"]
        except: print("Failed to set temperature_threshold, using default: ", varinit.temperature_threshold)
        try: varinit.socket_timeout = ver_txt["socket_timeout"]
        except: print("Failed to set socket_timeout, using default: ", varinit.socket_timeout)
    except:
        varinit.new_version_available = 0
        print("Failed to verify latest version")

def start_ap():
    try:
        #wifi.radio.start_ap(ssid=varinit.ap_name, password=str(pwd_gen()), authmode=(wifi.AuthMode.PSK, wifi.AuthMode.WPA2))
        ap_name = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] # mac-id för hotspot
        ap_name = str(ap_name)
        wifi.radio.start_ap(ssid=ap_name)
        #wifi.radio.start_dhcp_ap() # Removed DHCP, maybe causing bug http://None ?
        print("Started AP: ", varinit.ap_name)#,pwd_gen())
    except Exception as e: print("Failed to start AP: ", e)

def scan():
    netlist = []
    for networks in wifi.radio.start_scanning_networks(start_channel=1, stop_channel=14):
        if not networks.ssid == varinit.settings["ssid"]: netlist.append(networks.ssid)
        print(networks.ssid)
    wifi.radio.stop_scanning_networks()
    return(netlist)

def disp_init():
    varinit.tg1, varinit.tg2 = displayio.TileGrid(top, pixel_shader=palette), displayio.TileGrid(bottom, pixel_shader=palette)
    varinit.tg3 = displayio.TileGrid(topbottom, pixel_shader=palette)
    varinit.group = displayio.Group()
    tg1group, tg2group = displayio.Group(), displayio.Group()
    tg1group.append(varinit.tg1); tg2group.append(varinit.tg2)
    varinit.group.append(tg1group); varinit.group.append(tg2group)
    tg3group = displayio.Group()
    tg3group.append(varinit.tg3)
    varinit.group.append(tg3group)
    varinit.tg1.x = 0; varinit.tg1.y = 0
    varinit.tg2.x = varinit.if_long; varinit.tg2.y = 16
    varinit.tg3.y = 32
    varinit.palette[2] = (50,50,50)    # vit
    varinit.palette[3] = 0x000765      # morkbla
    varinit.palette[4] = (100,0,0)     # rod
    varinit.palette[5] = (20,20,20)    # grå
    varinit.palette[6] = (20,20,20)    # grå
    varinit.palette[7] = (0,20,0)    # grå
    varinit.display.root_group = varinit.group
    varinit.text = load_text()
    # Destination text smooth-scroll TileGrids (one bitmap per row, transparent background)
    _max_rows = max(8, varinit.if_tall // 6)
    _dest_bmp_w = max(400, varinit.if_long * 3)
    _dest_palette = displayio.Palette(2)
    _dest_palette[0] = 0x000000
    _dest_palette.make_transparent(0)
    _dest_palette[1] = 0xFF6600  # will be updated by colors()
    varinit.dest_palette = _dest_palette
    varinit.dest_bmps = [displayio.Bitmap(_dest_bmp_w, 13, 2) for _ in range(_max_rows)]
    varinit.dest_tgs = [displayio.TileGrid(varinit.dest_bmps[i], pixel_shader=_dest_palette, x=0, y=0) for i in range(_max_rows)]
    _dest_tg_group = displayio.Group()
    for _dtg in varinit.dest_tgs:
        _dtg.hidden = True
        _dest_tg_group.append(_dtg)
    varinit.group.append(_dest_tg_group)
    # Overlay TileGrid: line ID + minutes text drawn on top of dest TileGrids (transparent bg)
    varinit.overlay_palette = displayio.Palette(10)
    for _i in range(10): varinit.overlay_palette[_i] = varinit.palette[_i]
    varinit.overlay_palette.make_transparent(0)
    varinit.overlay_bmp = displayio.Bitmap(topbottom.width, topbottom.height, 10)
    varinit.overlay_tg = displayio.TileGrid(varinit.overlay_bmp, pixel_shader=varinit.overlay_palette, x=0, y=0)
    varinit.overlay_tg.hidden = True
    _overlay_group = displayio.Group()
    _overlay_group.append(varinit.overlay_tg)
    varinit.group.append(_overlay_group)
    varinit.dest_scroll_state = {}  # row_x -> {"overflow": int, "pos": int, "pause_end": float, "start_x": int}
    #if varinit.if_long > 128: varinit.palette[2] = (50,30,0)      # svart


def refresh(times = 2):
    if cpver == 9 and microcontroller.cpu.frequency == 160000000:
        if varinit.if_long > 128: return display.refresh(minimum_frames_per_second=0)
        if varinit.tg2.x > 64:
            time.sleep(0.001) ########## REMOVED for smoother scroll
        display.refresh(minimum_frames_per_second=0)
        delay = 0.002
        if not int(varinit.settings["scroll"]): return
        if varinit.tg2.x > 64:
            time.sleep(0.001) ########## REMOVED for smoother scroll
        for i in range(2 + int(varinit.settings["scroll"])):
            if varinit.cpver == 9: time.sleep(delay)
            display.refresh(minimum_frames_per_second=0)
    else:
        for i in range(times): display.refresh(minimum_frames_per_second=0)

def lights(switch):    
    varinit.group.hidden = True
    if switch: colors()

def nightcheck(force=False, _switch=False, turnon=False):
    if not check_timer(): 
        varinit.group.hidden = 1
        return


    if _switch: varinit.on_off_counter = 1 - varinit.on_off_counter
    if turnon: 
        varinit.group.hidden = 1 - varinit.group.hidden
        varinit.shared["nightcount"] = 0
        return
    
    if force: return lights(True)
    elif varinit.on_off_counter == 0 or int(varinit.settings["sleep"]) == 1 and varinit.shared["nightcount"] > 1:
        if not varinit.group.hidden: return lights(False)
    else: lights(True)
    
def fetch_data(host, port=80, args="", headers = "", filetype="text"):
    if varinit.if_long > 128 and not int(varinit.settings["listmode"]): version_delay(slowdown=1)
    
    data = ""
    cache = ""
    try: _from = binascii.hexlify(varinit.settings["stations"]["1"]["mystation"]).decode("utf-8")
    except: _from = binascii.hexlify(bytearray(varinit.settings["stations"]["1"]["mystation"])).decode("utf-8")
    headers = "User-Agent: " + str(id) + "\r\n"
    headers += "Accept: application/json\r\n" + "Content-Type: application/json\r\n" + "Host: " + host + "\r\n" + "Version: " + str(varinit.settings["version"]) + "\r\n"
    headers += "Uptime: " + str(round((time.monotonic() - varinit.starttime)/60)) + "\r\n"
    headers += "OS-Version: " + str(varinit.cpver) + "\r\n"
    headers += "Country: " + str(varinit.settings["stations"]["1"]["country"]) + "\r\n"
    headers += "Operator: " + str(varinit.settings["stations"]["1"]["operator"]) + "\r\n"
    headers += "Siteid: " + str(varinit.settings["stations"]["1"]["siteid"]) + "\r\n"
    headers += "From: " + str(_from) + "\r\n"
    headers += "Version: " + "d" + str(varinit.version) + "\r\n"
    headers += "User: " + str(varinit.settings["user"]) + "\r\n"
    headers += "Temperature: " + str(round(microcontroller.cpu.temperature))
    print("-Fetching------------------------------------------------ ")
    print("■ HOST: ", host)
    print("■ ARGS: ", args)
    print("■ PORT: ", port)
    print("■ FILETYPE: ", filetype)
    request = b"GET " + args + " HTTP/1.0\r\n" + headers + "\r\n\r\n"
    try:
        #with pool.socket(pool.AF_INET, pool.SOCK_STREAM) as s:
        with pool.socket() as s:
            cache = bytearray(1024)                                # MAX FILESIZE
            #s.setblocking(False)
            s.settimeout(varinit.socket_timeout)
            s.connect((host, port))
            sent = s.sendall(request)
            #buff = bytearray(512)
            buff = bytearray(512)
            data = s.recv_into(buff)
            while data:
                cache += buff[:data]
                data = s.recv_into(buff)
    except Exception as e: 
        print("Socket error: ", e)
        #if "-2" in str(e): reset()
        #if "-2" in str(e): wifi.radio.enabled = False                  ######## TESTAR
            
    except: print("Socket error")
    try:
        if filetype == "binary":
            separator = b'\r\n\r\n'
            index = cache.find(separator)
            if index != -1: cache = cache[index+len(separator):]
            return cache
        x = cache.decode("utf-8")
        data = x.split("\r\n\r\n",1)[1]
    except: print("Reading error")
    
    try:
        date = x.split("Date:",1)[1]
        date = date.split("\r\n")[0]
        varinit.currenttime = convert_date(date)
    except: pass
    print("--------------------------------------------------------- ")
    if varinit.if_long > 128 and not int(varinit.settings["listmode"]): version_delay(slowdown=2)
    #print("DATA ", data)
    return data

def sort_by_minutes(lst):
    def get_minutes(sub_lst): return int(sub_lst[3].split()[0])
    lst.sort(key=get_minutes)
    return lst

def sort_by_hours(lst):
    def __sort(lst):
        return sorted(lst, key=lambda x: x[3])

    if "23:" in str(lst):
        lst = json.dumps(lst)
        lst = json.loads(lst.replace("00:", "24:"))
        lst = __sort(lst)
        lst = json.dumps(lst)
        lst = json.loads(lst.replace("24:", "00:"))
        return lst
    return __sort(lst)


def _converttime(ts, age = 0): return time.mktime(time.struct_time((int(ts[:4]),int(ts[5:7]),int(ts[8:10]),int(ts[11:13]),int(ts[14:16]),int(ts[17:19]) + int(age),0,-1,-1)))

def traffic_parser(data, traffic_type, num="1"):
    ## Vänder "DIRECTION" på BUSES och TRAINS ##############
    stn = varinit.settings["stations"][num]
    direction = int(stn["direction"])
    night_buses_only = int(stn["buses_option"])
    if traffic_type in ("TRAIN", "BUS", "TRAM") and direction:
        direction = 3 - direction
    ########################################################
    print(" >>", traffic_type)
    dataout = []
    _maxdest = int(varinit.settings["maxdest"])
    if int(varinit.settings["listmode"]): _maxdest = varinit.if_tall // 8
    #show_lines = varinit.settings["show_lines"]
    #has_line_filter = isinstance(show_lines, list) and len(show_lines) > 0
    clocktime = varinit.settings["clocktime"]
    rt_indicator = varinit.settings["rt_indicator"]
    offset = int(stn["offset"])
    try: 
        if not data["departures"] and "msg" in data:
            return [["1", data["msg"], "***","",""]]
    except: pass
    for all in data["departures"]:
        if len(dataout) > _maxdest: break
        line = all["line"]
        if traffic_type != line["transport_mode"]: continue
        if traffic_type == "BUS" and stn["operator"] == "sl" and night_buses_only:
            if str(line["id"])[-2:-1] != "9":
                continue
        if len(str(varinit.settings["show_lines"])) > 4:
            print(str(varinit.settings["show_lines"]))
            if not all["line"]["id"].lower() in varinit.settings["show_lines"]: continue
        difference = _converttime(all["expected"]) - varinit.currenttime
        if difference < 0: continue
        minsleft = str(round(difference/60))
        if int(minsleft[:2]) > offset:  
            if line["transport_mode"] == "ZET":
                if int(line["id"]) < 18:
                    line["transport_mode"] = "TRAM"
                else: line["transport_mode"] = "BUS"

            if not int(all["direction_code"]) or not int(direction) or int(direction) == int(all["direction_code"]):
                _minsleft = str(all["expected"].split("T")[1][:5]) if clocktime else minsleft
                if line["id"] == "0": line["id"] = ""
                try: 
                    delay = all["deviations"][0] if rt_indicator else ""
                except: delay = ""
                dep = ["0", str(line["id"]), delay + all["destination"], _minsleft, str(all["direction_code"])]
                _strip_dest = varinit.settings.get("strip_dest", [])
                if isinstance(_strip_dest, list):
                    for _sd in _strip_dest:
                        if _sd: dep[2] = dep[2].replace(_sd, "").strip()
                if traffic_type != "METRO":
                    if line["transport_mode"] == traffic_type:
                        dep[2] = dep[2].split('(')[0]
                        dataout.append(dep)
                elif line["transport_mode"] == traffic_type:
                    if stn["operator"] != "sl":
                        dataout.append(dep)
                    else:
                        line_id = int(line["id"])
                        if (int(stn["green"]) and line_id in (17, 18, 19)) or \
                           (int(stn["red"]) and line_id in (13, 14)) or \
                           (int(stn["blue"]) and line_id in (10, 11)):
                            dataout.append(dep)
    return dataout

def get_departure(num = "1", dataout = [["1", "^ Data error","","",""]]):
    
    if varinit.settings["stations"][num]["siteid"] == "00" or not varinit.settings["stations"][num]["operator"]: return [["1", dicts.language[varinit.settings["language"]]["settings"]["select_operator"], "***","",""]]
    if varinit.settings["stations"][num]["siteid"] == "0": return [["1", dicts.language[varinit.settings["language"]]["settings"]["search"], "***","",""]]
    if varinit.settings["stations"][num]["siteid"] == "000": return [["1", dicts.language[varinit.settings["language"]]["display"]["select_station"], "***","",""]]
    if time.monotonic() > varinit.show_station_timer + varinit.show_station_interval and not varinit.shared["nightcount"]:
        if "demo" in os.listdir() or int(settings["show_my_station"]):
            _out = varinit.text[4]+ settings["stations"][num]["mystation"]
            if "demo" in os.listdir(): _out = "%-Skylt.se"
            if not varinit.settings["listmode"]: renderstring(_out, 1,0,1, _cls=top)
            else: renderstring(_out, 100, 0, 1)
        varinit.show_station_timer = time.monotonic()
    if varinit.use_cached_data and num in varinit.cached_departure_data:
        data = varinit.cached_departure_data[num]
        varinit.use_cached_data = False
        print("■ Using cached data for station", num)
    else:
      try: 
        temperature_check()
        _data = fetch_data(host="data.t-skylt.se", port=90, args='/get_departures?country=' + varinit.settings["stations"][num]["country"] + '&operator=' + varinit.settings["stations"][num]["operator"] + "&station=" + str(varinit.settings["stations"][num]["siteid"]))
        if _data: data = json.loads(_data)
        else: 
            varinit.active_message = True
            if str(wifi.radio.ipv4_address) == "0.0.0.0":   ########
                pass#wifi.radio.enabled = False                  ######## TESTAR
            return [["1", "-","","",""]]
      except Exception as e: 
        cls(topbottom)
        print(e)
        varinit.active_message = True
        errno = type(e).__name__
        try:
            if varinit.settings["debug"]: return [["1", str(errno) + " " + str(e),"","",""]] 
        except: pass
        err_msg = "*"
        if errno == "TypeError": err_msg = "**"
        if errno == "ValueError": err_msg = "***"#dicts.language[varinit.settings["language"]]["display"]["decoding_error"]
        print("Avkodningsfel: ", errno)
        return [["1", err_msg,"","",""]]
      except: 
        cls(topbottom)
        varinit.active_message = True
        print("Avkodningsfel.")
        return [["1", "^ Unknown error: 1","","",""]]
      varinit.cached_departure_data[num] = data
    try:
        dataout = []
        print("■", varinit.settings["stations"][num]["mystation"], varinit.settings["stations"][num]["siteid"])
        for t_types in varinit.traffic_dict:
            if varinit.settings["stations"][num][t_types]: dataout.extend(traffic_parser(data, t_types, num))
        if not varinit.settings["clocktime"]: dataout = sort_by_minutes(dataout)[slice(varinit.settings["maxdest"])]
        else: dataout = sort_by_hours(dataout)[slice(varinit.settings["maxdest"])]
        print(*dataout, sep='\n')
    except Exception as e: 
        print(e)
        cls(topbottom)
        try:
            if not data["departures"] and "msg" in data: return [["1", data["msg"], "***","",""]]
        except: pass
        return [["1", dicts.language[varinit.settings["language"]]["settings"]["no_data"],"***","",""]]
    return dataout

def merge_departures(nums):
    # Fetch each configured stop's departures and merge them into one list,
    # sorted by departure time, for devices too narrow to show separate lists side by side.
    combined = []
    fallback_msg = None
    for num in nums:
        stn = varinit.settings["stations"].get(num)
        if not stn: continue
        if stn["siteid"] in ("00", "0", "000", "") or not stn["operator"]: continue
        rows = get_departure(num=num)
        if rows and rows[0][0] == "1":
            fallback_msg = rows
            continue
        combined.extend(rows)
    if not combined:
        if fallback_msg: return fallback_msg
        return [["1", dicts.language[varinit.settings["language"]]["display"]["no_more_departures"], "***", "", ""]]
    if not varinit.settings["clocktime"]: combined = sort_by_minutes(combined)
    else: combined = sort_by_hours(combined)
    return combined[slice(varinit.settings["maxdest"])]

def abbreviate_dest(text, max_px):
    # Only shorten when the destination would otherwise be truncated; leaves short names untouched.
    if strlen(text) <= max_px: return text
    for pair in varinit.settings.get("dest_abbrev", []):
        if not isinstance(pair, list) or len(pair) != 2: continue
        long, short = pair
        if long and long in text:
            text = text.replace(long, short)
            if strlen(text) <= max_px: return text
    return text

def reformat_data(trainlist):
    def top_screen_filter(tlist):
        try: tlist[1] = tlist[1][:varinit.settings["line_length"]]
        except: pass
        if not varinit.settings["clocktime"]: tlist[3] += varinit.settings["mins"]
        spacing = "((((((((("
        if varinit.if_long == 128:
            spacing = "((("
            if tlist[2] in station_names_dict:
                tlist[2] = station_names_dict[tlist[2]]
            else: 
                for items in dicts.replace_list_destinations:
                    if strlen(tlist[2]) > 75: tlist[2] = tlist[2].replace(items[0], items[1])

        # Keep the top row non-scrolling text from colliding with minutes-left text.
        # Measure widths with the top-row (large) font so fitting is stable.
        def _strlen_top(s):
            f = fonts[0]
            total = 0
            for c in s:
                if c in f:
                    total += f[c][0]
                else:
                    total += f["_"][0]
            return total

        max_left_w = max(0, varinit.if_long - _strlen_top(tlist[3]))

        # First consume extra gap before touching destination text.
        while len(spacing) > 1 and _strlen_top(tlist[1] + spacing + tlist[2]) > max_left_w:
            spacing = spacing[:-1]

        max_dest_w = max_left_w - _strlen_top(tlist[1] + spacing)
        if max_dest_w < 0:
            max_dest_w = 0

        if _strlen_top(tlist[2]) > max_dest_w:
            if max_dest_w <= 0:
                tlist[2] = ""
            else:
                trimmed = tlist[2]
                while trimmed and _strlen_top(trimmed + ".") > max_dest_w:
                    trimmed = trimmed[:-1]
                tlist[2] = trimmed + ("." if trimmed and trimmed != tlist[2] else "")

        offs = varinit.if_long - (strlen(tlist[3]) + strlen(tlist[1] + spacing + tlist[2]))
        if int(trainlist[0][0]): return trainlist
        
        #if varinit.if_long > 128: renderstring(tlist[1] + spacing + tlist[2] + ("(" * offs) + tlist[3], 1)
        #else:
        #    offs = 128 - strlen(tlist[3])
        #    renderstring(offs*"(" + tlist[3], 1)
        #    renderstring(tlist[1] + spacing + tlist[2], 1)
        
        offs = max(0, varinit.if_long - strlen(tlist[3]))
        renderstring(offs*"(" + tlist[3], 1)
        renderstring(tlist[1] + spacing + tlist[2], 1)

        return trainlist[1:]
    spacing = "" if varinit.if_long == 128 else "(("
    long_buffer = "("*120 if varinit.if_long > 128 else ""
    if not len(trainlist):                                                                             
        cls(top)
        cls(bottom)
        return varinit.text[6]
    if trainlist[0][0] == "1": return trainlist[0][1] + "  " + trainlist[0][2] + "  " + trainlist[0][3]  
    elif int(varinit.settings["listmode"]): return trainlist
    else: return long_buffer + "         ".join(["  ".join([a[1][:varinit.settings["line_length"]] + (spacing * 2), a[2] + (6 * spacing), a[3] + (varinit.settings["mins"] if not varinit.settings["clocktime"] else "") + (spacing * 10)]) for a in top_screen_filter(trainlist[0])])

def renderstring(_string, screen_partition = 0, min = 0, slow = 0, invertcolor = 0, shading=False, smallfont=False, sys_msg=False, shade=False, large=False, _cls=False, _refresh=False, ontop=False, block=False, logo=False, mini=False, start_x=0, clip_x=None, target_bmp=None, target_offs=None):
    
    if varinit.settings["long"] == -1: 
        mini = True
    if varinit.rotated:
        mini = True
    if varinit.display.width <= 64:
        mini = True
    
    if sys_msg: font_before = varinit.currentfont
    cls(_cls) if _cls else None
    #print("LEN: ", len(_string), _string, type(_string))
    if dicts.language[varinit.settings["language"]]["display"]["no_more_departures"] in _string: varinit.shared["nightcount"] += 1 
    elif str(_string) == "-" or str(_string) == "*": pass # testing
    else:
        if varinit.shared["nightcount"] > 1: varinit.on_off_counter = 1
        varinit.shared["nightcount"] = 0
    nightcheck()
    _color = False
    offs = 2
    pixwidth = start_x
    
    if not ontop and not varinit.settings["listmode"] and sys_msg:
        varinit.currentfont = 1
        varinit.tg3.y = 0
        
    if ontop: 
        screen_partition = 1
        if varinit.settings["listmode"]: offs = 0
    elif smallfont: varinit.currentfont = 1
    elif large: varinit.currentfont = 0
    
    
    if varinit.currentfont or screen_partition > 2: screen_location = [topbottom, topbottom, topbottom, topbottom]
    else: screen_location = [bottom, top, top, bottom]
    
    if screen_partition > 2: 
        _row_step = 6 if mini else (13 if varinit.currentfont == 0 else 8)
        offs = int(str(screen_partition)[1:]) * _row_step
        screen_partition = 0
    
    
    if sys_msg == "red": _color = (0,4)
    elif sys_msg == "blue": _color = (0,3)
    elif sys_msg == "green": _color = (0,7)
    elif sys_msg == "white": _color = (0,2)
    elif sys_msg == "yellow": _color = (0,1)
    
    font = fonts[varinit.currentfont]
    if smallfont == True: font = fonts[1]
    shade = False
    shading_width = 15
    _write_bmp = target_bmp if target_bmp is not None else screen_location[screen_partition]
    _write_offs = target_offs if target_offs is not None else offs
    
    if not sys_msg and int(varinit.settings["listcolor"]): shade = True
    if not sys_msg and wifi.radio.connected == False: 
        shade = True
        shading_width = 8
    
    
    for character in _string:
        if mini:
            character = character.lower()
            varinit.currentfont = 2
            font = fonts[varinit.currentfont]

        # LOGO_CHAR is only defined in fonts updated to carry the logo glyph;
        # older font files (or a font not yet updated) still hold it under
        # "%", so fall back per-character against whichever font renders it.
        if character == LOGO_CHAR and LOGO_CHAR not in font: character = "%"
        if not character in font: character = "_"
        
        for width in range(font[character][0]):
            for height in range(font["fontheight"]):
                invertedwidth = font[character][0] - width
                if isinstance(font[character][1],int):
                    try: color = (font[character][height+1] >> invertedwidth) & 1
                    except: color = color
                    
                    #if logo and color == 1: color = 5
                    #if invertcolor and int(varinit.settings["listmode"]) and pixwidth > 98: color = 1 - color
                    if invertcolor == 2: color = 1 - color
                    if _color:
                        if not int(color): color = _color[0]
                        else: color = _color[1]
                    if clip_x is None or width + pixwidth < clip_x:
                        try: _write_bmp[width+pixwidth,(height)+_write_offs] = color
                        except: pass
                else: 
                    __color = int(font[character][height+1][width])
                    if varinit.settings["long"] == 1:
                        if __color == 5: __color = 1
                    
                    if clip_x is None or width + pixwidth < clip_x:
                        try: _write_bmp[width+pixwidth,(height)+_write_offs] = __color
                        except: pass
            if slow: varinit.display.refresh(minimum_frames_per_second=0)
        if isinstance(font[character][1],int):
            pixwidth += font[character][0]
        else: pixwidth += len(font[character][1])
    if _refresh: refresh()
    if sys_msg: varinit.currentfont = font_before
    return(pixwidth)

def scroll_mode():
    if varinit.matrix.height == 64: microcontroller.cpu.frequency = 180000000
    if varinit.if_long > 128: version_delay(slowdown=2)
    nightcheck()
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = 0, 16, 32
    direction = varinit.text[9]
    scroll_buff = varinit.text[1]
    if varinit.shared["loop_counter"] == -7: reset()
    elif varinit.shared["loop_counter"] == -5:
        varinit.font = varinit.fonts[0]
        _logo = varinit.text[0]# if "boot.py" in os.listdir() else "% DEBUG"
        
        renderstring(_logo, 1, 0, 1, large=True, block=True, logo=True)
        wifiattempt()
        #check_version()
        varinit.first_start = False
        if varinit.settings["long"] == -1:
            varinit.settings["listmode"] = 1

        if varinit.new_version_available == 1: scroll_buff += " -    ^ " + dicts.language[varinit.settings["language"]]["display"]["new_version_available"] + str(varinit.new_ver)
        varinit.scrollsum = renderstring(scroll_buff, _cls=bottom)
        
    elif varinit.shared["loop_counter"] == -4:        
        if "textfil.txt" in os.listdir():
            
            try:
                varinit.scrollsum = renderstring(varinit.textfil.pop(0), _cls=bottom)
            except: 
                renderstring("Läser in text...", 1, 0, large=True, _cls=top)
                varinit.scrollsum = renderstring("***", _cls=bottom)
                with open("textfil.txt") as f:
                    varinit.textfil = f.read().splitlines()
                print(varinit.textfil)
                renderstring("", 1, 0, large=True, _cls=top)
            varinit.shared["loop_counter"] = -5
            
            print("TEXT")
        else:
            renderstring(str(varinit.text[2]), 1, 0, large=True)
            varinit.scrollsum = renderstring(varinit.text[3]+str(wifi.radio.ipv4_address)+"         ", _cls=bottom)


    elif varinit.shared["loop_counter"] == -3:   
        
        
        renderstring(varinit.text[4]+ varinit.settings["stations"]["1"]["mystation"][:16], 1, 0, large=True, _cls=top)
        if varinit.settings["direction"] == 1: direction = varinit.text[10]
        elif varinit.settings["direction"] == 2: direction = varinit.text[11]
        ifoffset = " + " + str(varinit.settings["stations"]["1"]["offset"]) + varinit.settings["mins"] if int(varinit.settings["stations"]["1"]["offset"]) else ""
        varinit.text[5] = direction + "   >   " + str(varinit.settings["maxdest"]) + dicts.language[varinit.settings["language"]]["display"]["departures"] + ifoffset
        varinit.scrollsum = renderstring(varinit.text[5], large=True, _cls=bottom)
        varinit.shared["loop_counter"] = -2
    varinit.tg2.x = varinit.if_long
    varinit.shared["loop_counter"]+=1
    if varinit.shared["loop_counter"] > 0:
        if varinit.active_message == True:
            reset_scroll()
            varinit.active_message = False
        elif time.monotonic() > varinit.shared["scroll_timer"] + updatedelay:
            cls(bottom, _refresh=True)
            if time.monotonic() > varinit.ad_timer + varinit.ad_delay * 60 and varinit.shared["nightcount"] < 2:
                try: 
                    ad = ad_message() 
                    if ad: 
                        varinit.scrollsum = renderstring(reformat_data([["1", ad,"***","",""]]), large=True, _cls=bottom)
                        varinit.active_message = True
                    else: varinit.scrollsum = renderstring(reformat_data(get_departure()), large=True)
                except: varinit.scrollsum = renderstring(reformat_data(get_departure()), large=True)
            
            elif time.monotonic() > varinit.deviations_timer + (varinit.deviations_delay * 60) \
                and int(varinit.settings["show_msgs"]) and varinit.shared["nightcount"] < 2 \
                and varinit.settings["stations"]["1"]["operator"] in ["sl","vt"]:
                try: varinit.scrollsum = renderstring(reformat_data([["1", get_deviations(),"***","",""]]), large=True, _cls=bottom)
                except: varinit.scrollsum = renderstring(reformat_data([["1", " ","***","",""]]), large=True, _cls=bottom)
                varinit.deviations_timer = time.monotonic()
                varinit.active_message = True
            else: varinit.scrollsum = renderstring(reformat_data(get_departure()), large=True)
            rnd = random.randint(0, 10)
            varinit.shared["scroll_timer"] = time.monotonic() + rnd
            print("RND: ", rnd)

CLOCK_ROW_MARK = "__clock__"
MSG_ROW_MARK = "__msg__"

def clock_string():
    t = time.localtime(varinit.currenttime)
    def _z(n):
        s = str(n)
        return "0" + s if len(s) == 1 else s
    hhmm = _z(t[3]) + ":" + _z(t[4])
    if int(varinit.settings.get("clock_row_date", 0)):
        datepart = _z(t[2]) + "." + _z(t[1]) + "." + _z(t[0] % 100)
        return datepart + " * " + hhmm
    return hhmm

def apply_clock_row(trainlist, is_clock_station=True):
    # Reserves the same row position (top or bottom) in every station's list,
    # so the clock can use the full display width in half mode without a
    # neighboring station ever having a real departure sharing that row.
    if not int(varinit.settings.get("show_clock_row", 0)): return trainlist
    # wrap a message string into a row so it still leaves room for the clock row below
    if isinstance(trainlist, str):
        trainlist = [["", "", trainlist[:40], "", MSG_ROW_MARK]]
    if not isinstance(trainlist, list) or not trainlist: return trainlist
    if not isinstance(trainlist[0], list): return trainlist
    n = max(1, int(varinit.settings.get("maxdest", 1)))
    kept = trainlist[:max(0, n - 1)]
    reserved_row = ["0", "", clock_string() if is_clock_station else "", "", CLOCK_ROW_MARK]
    if varinit.settings.get("clock_row_position", "bottom") == "top":
        kept.insert(0, reserved_row)
    else:
        kept.append(reserved_row)
    return kept

def list_mode(mini=False, half=False):
    mini = varinit.settings["mini"]

    #### debug
    #mini = True
    if varinit.rotated:
        mini = True
        half = False
    elif varinit.display.width <= 64:
        mini = True
        half = False
    elif varinit.settings["multiple"]: 
        half = True
        mini = True
    if varinit.settings["long"] == -1 and not varinit.rotated: 
        mini = True
        half = True
     


    if varinit.if_long > 128: version_delay(slowdown=1)
    large_list = not mini and not half and not varinit.rotated and int(varinit.settings.get("large_list", 0))
    xs_line_id = varinit.display.width <= 64 and not varinit.rotated and int(varinit.settings.get("xs_line_id", 0))
    multi_station_line_id = half and not varinit.rotated and varinit.display.width > 64 \
                    and int(varinit.settings.get("multi_station_line_id", 0)) and int(varinit.settings["line_length"])
    _show_line = not varinit.rotated and (varinit.display.width > 64 or xs_line_id) \
                 and (not half or multi_station_line_id)
    varinit.currentfont = 1
    if mini: varinit.currentfont = 2
    elif large_list: varinit.currentfont = 0
    extrarow = 1 if mini else 0
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = extrarow + 0-32, extrarow + 16-32, extrarow + 0

    _dest_scroll = int(varinit.settings.get("dest_scroll", 0))
    _now = time.monotonic()
    cls(topbottom)
    # Hide dest TileGrids and overlay; will be shown per-row if dest_scroll active
    try:
        for _dtg in varinit.dest_tgs: _dtg.hidden = True
        varinit.overlay_tg.hidden = True
        varinit.overlay_bmp.fill(0)
        varinit.dest_scroll_state = {}
    except: pass

    if varinit.shared["startup"]:
        list_splash()
        varinit.shared["startup"] = False
        return time.monotonic() - varinit.updatedelay + 2
    if varinit.shared["loop_counter"] == -7: reset()
    if time.monotonic() > varinit.ad_timer + varinit.ad_delay * 60 and varinit.shared["nightcount"] < 2:
        try: 
            ad = ad_message()
            if ad:
                index = 0
                for i in range(0, 4):
                    _ad = ad[index:index+15].lstrip(" ")
                    renderstring(str(_ad), 100+i, shading=True, smallfont=True)
                    refresh()
                    index += 15
            else: return 0
        except: pass
        return time.monotonic() - varinit.updatedelay + 2
    
    # trainlist = reformat_data(get_departure())
    ### DEBUG
    
    _r = 1
    try:
        if varinit.settings["multiple"]:
            if varinit.settings["long"] == 0: _r = 2
            if varinit.settings["long"] == 1: _r = 3
        else: _r = 1
    except: pass

    # Each station gets an equal share of the physical display, so a device
    # with spare panels (e.g. the XL's three panels showing only 2 stations)
    # spreads its stations across the full width.
    # COL_MARGIN keeps a small gap at the column's edges; the rest
    # of the column is filled by the natural gap between the destination
    # and the time, so a wider column just reads as more breathing room.
    col_w = varinit.if_long // _r
    COL_MARGIN = 2

    merge_list_mode = int(varinit.settings["multiple"]) and varinit.display.width <= 64 and not varinit.rotated
    if merge_list_mode:
        print("Fetching merged stops")
        varinit.traindata[1] = apply_clock_row(reformat_data(merge_departures(("1", "2", "3"))))
    else:
        for i in range(_r):
            print("Fetching: ", i+1)
            _data = reformat_data(get_departure(num = str(i+1)))
            varinit.traindata[i+1] = apply_clock_row(_data, is_clock_station=(i == 0))
            if not half or i+1 == _r: break
        
    
    
    
    try:
        for record in varinit.traindata:
            print(record)
            trainlist = varinit.traindata[record]
            if isinstance(trainlist, list):
                trainlist = [row[:] for row in trainlist if isinstance(row, list)]
            if int(record) > _r: continue
            if not half and "str" in str(type(trainlist)): 
                sysprint("".join(trainlist[:30]), 100)
                if dicts.language[settings["language"]]["display"]["no_more_departures"] in trainlist: return time.monotonic()
                return time.monotonic() - varinit.updatedelay + 2
            elif "str" in str(type(trainlist)): 
                print(trainlist)
                #sysprint("".join(trainlist[:30]), 100)
                trainlist = [["","",trainlist[:40],"",MSG_ROW_MARK]]
                    #continue
                #if dicts.language[settings["language"]]["display"]["no_more_departures"] in trainlist: 
                #    return time.monotonic()
                #if not half: return time.monotonic() - varinit.updatedelay + 2
        
            if (large_list or multi_station_line_id) and isinstance(trainlist, list):
                _max_lw = 0
                for _a in trainlist:
                    if isinstance(_a, list) and len(_a) > 1:
                        _w = strlen(_a[1][:varinit.settings["line_length"]])
                        if _w > _max_lw: _max_lw = _w
                if large_list: line_col = _max_lw + 6
                else: line_col = _max_lw + 2 if _max_lw else 0
            else:
                line_col = 0

            _xs_max_lw = 0
            if xs_line_id and isinstance(trainlist, list):
                for _a in trainlist:
                    if isinstance(_a, list) and len(_a) > 1:
                        _w = strlen(_a[1][:varinit.settings["line_length"]])
                        if _w > _xs_max_lw: _xs_max_lw = _w

            for x, all in enumerate(trainlist):

                is_clock_row = len(all) > 4 and all[4] == CLOCK_ROW_MARK
                is_msg_row = len(all) > 4 and all[4] == MSG_ROW_MARK
                if is_clock_row and int(record) != 1: continue
                all[2] = all[2].split('(')[0].split(" via")[0]#.lower()
                _strip_dest = varinit.settings.get("strip_dest", [])
                if isinstance(_strip_dest, list):
                    for _sd in _strip_dest:
                        if _sd: all[2] = all[2].replace(_sd, "").strip()
                if strlen(all[2]) > 82 and varinit.if_long == 128:
                    for items in dicts.replace_list_destinations:
                        all[2] = all[2].replace(items[0], items[1])
                    try: all[2] = station_names_dict[all[2]]
                    except: pass

                mins_cut = 23 - len(varinit.settings["mins"]) - (int(varinit.settings["line_length"]))

                if len(all[3]) > 1:
                       mins_cut -= 1

                if not varinit.settings["clocktime"]:
                    _mins_ref_w = strlen("00")
                    if strlen(all[3]) < _mins_ref_w:
                        all[3] = (_mins_ref_w - strlen(all[3])) * "(" + all[3]

                if_not_clocktime = (
                    varinit.settings["mins"]
                    if all[3] and not varinit.settings["clocktime"] and not (is_clock_row or is_msg_row)
                    else ""
                )

                all[3] += if_not_clocktime

                _full_dest_w = 0
                _max_px = 0
                _line_col_w = 0
                if varinit.rotated or varinit.display.width <= 64:
                    _w = varinit.if_long if varinit.rotated else varinit.display.width
                    _max_px = _w - strlen(all[3])
                    if not varinit.rotated and xs_line_id and not (is_clock_row or is_msg_row):
                        _max_px -= _xs_max_lw + 2
                    all[2] = abbreviate_dest(all[2], _max_px)
                    while len(all[2]) > 0 and strlen(all[2]) > _max_px:
                        all[2] = all[2][:-1]
                elif large_list:
                    _max_px = varinit.if_long - strlen(all[3]) - line_col
                    _font = fonts[varinit.currentfont]
                    all[2] = abbreviate_dest(all[2], _max_px)
                    while len(all[2]) > 0 and sum(_font.get(c, _font['_'])[0] for c in all[2]) > max(0, _max_px):
                        all[2] = all[2][:-1]
                elif not half:
                    _line_col_w = 0 if (is_clock_row or is_msg_row) else strlen(varinit.settings["line_length"] * ("((((" if mini else "(((((("))
                    _max_px = varinit.if_long - strlen(all[3]) - _line_col_w - 2
                    _full_dest_w = strlen(all[2])
                    if not (_dest_scroll and _full_dest_w > max(0, _max_px)):
                        all[2] = abbreviate_dest(all[2], _max_px)
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                if half:
                    if is_clock_row:
                        # only column 1 ever renders this row (others `continue` above), so it
                        # can use the full display width rather than a single column's share
                        _max_px = varinit.if_long - strlen(all[3]) - 1
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                    elif is_msg_row:
                        _max_px = col_w - COL_MARGIN - strlen(all[3]) - 1
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                    elif multi_station_line_id:
                        _max_px = col_w - (COL_MARGIN * 2) - strlen(all[3]) - line_col - 1
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                    else:
                        all[2] = all[2][:15 - len(varinit.settings["mins"])]
                        if varinit.settings["clocktime"]:
                            all[2] = all[2][:11]
                mins = all[2]

                if mini: all[2] = mins
                all[1] = all[1][:varinit.settings["line_length"]]
                
                line = all[1]
                dest = all[2]
                
                if varinit.rotated:
                    offs = varinit.if_long - strlen(all[3])
                elif varinit.display.width <= 64:
                    offs = varinit.display.width - strlen(all[3])
                else: offs = varinit.if_long - strlen(all[3])
                if half:
                    all[3] = all[3].replace(" " + if_not_clocktime,"")
                    offs = col_w - COL_MARGIN - strlen(all[3])

                    

                minsleft = offs*"(" + all[3]
                
                inv = 0

                if half: minsleft = minsleft.replace(" " + if_not_clocktime, "")
                
                if half: multiple_offset = (int(record) - 1) * col_w
                else: multiple_offset = 0
        
                min_color = "white" if varinit.settings.get("listcolor_time", 0) or varinit.rotated else "yellow"
                lin_color = "yellow" if not varinit.settings["listcolor"] else "white"
                clock_color = varinit.settings.get("clock_row_color", "white")
                if varinit.rotated or varinit.display.width <= 64:
                    added_space = ""
                    line = ""
                    if not varinit.rotated and xs_line_id:
                        line = all[1][:varinit.settings["line_length"]]
                        added_space = (_xs_max_lw + 2) * "("
                elif mini:
                    added_space = varinit.settings["line_length"] * "(((("
                    if half: added_space = COL_MARGIN * "(" + (line_col * "(" if multi_station_line_id else "")
                else: added_space = varinit.settings["line_length"] * "(((((("
                if not varinit.settings["line_length"]:
                    added_space = ""
                    line = ""

                if is_clock_row:
                    _clock_align = varinit.settings.get("clock_row_align", "left")
                    _clock_avail = varinit.display.width if varinit.display.width <= 64 else varinit.if_long
                    _clock_pad = max(0, _clock_avail - strlen(dest))
                    if _clock_align == "center": _clock_pad = _clock_pad // 2
                    elif _clock_align == "left": _clock_pad = 0
                    added_space = _clock_pad * "("
                    line = ""
                elif is_msg_row:
                    added_space = ""
                    line = ""

                if large_list:
                    _lpart = 100 + x
                    _dest_pad = line_col * "("
                    renderstring(minsleft, _lpart, 0, 0, inv, sys_msg=min_color, start_x=multiple_offset)
                    renderstring(_dest_pad + dest, _lpart, 0, 0, inv, sys_msg=(clock_color if is_clock_row else False), start_x=multiple_offset)
                    if not half and not varinit.rotated: renderstring(line, _lpart, 0, 0, inv, sys_msg=lin_color, start_x=multiple_offset)
                    if x > 4: continue
                else:
                    _use_tg = (_dest_scroll and not half and not varinit.rotated
                               and varinit.display.width > 64
                               and _full_dest_w > max(0, _max_px))
                    if _use_tg:
                        # TileGrid smooth scroll: dest in dest_bmp, line+mins in overlay_bmp
                        _row_step = 6 if mini else 8
                        _overflow = _full_dest_w - _max_px
                        varinit.dest_bmps[x].fill(0)
                        renderstring(dest, 100+x, 0, 0, inv, mini=mini,
                                     target_bmp=varinit.dest_bmps[x], target_offs=0)
                        varinit.dest_tgs[x].x = _line_col_w
                        varinit.dest_tgs[x].y = extrarow + x * _row_step
                        varinit.dest_tgs[x].hidden = False
                        varinit.dest_scroll_state[x] = {
                            "overflow": _overflow, "pos": 0,
                            "pause_end": _now + x * 0.8 + 2.0, "start_x": _line_col_w
                        }
                        renderstring(minsleft, 100+x, 0, 0, inv, mini=mini,
                                     sys_msg=min_color, target_bmp=varinit.overlay_bmp, start_x=multiple_offset)
                        if _show_line:
                            renderstring(line, 100+x, 0, 0, inv, mini=mini,
                                         sys_msg=lin_color, target_bmp=varinit.overlay_bmp, start_x=multiple_offset)
                        varinit.overlay_tg.y = extrarow
                        varinit.overlay_tg.hidden = False
                    else:
                        renderstring(minsleft, 100+x, 0, 0, inv, mini=mini, sys_msg=min_color, start_x=multiple_offset)
                        renderstring(added_space + dest, 100+x, 0, 0, inv, mini=mini, sys_msg=(clock_color if is_clock_row else False), start_x=multiple_offset)
                        if _show_line:
                            renderstring(line, 100+x, 0, 0, inv, mini=mini, sys_msg=lin_color, start_x=multiple_offset)
                    if x > varinit.if_tall // 8 - 1: continue

    except Exception as e: print("ERROR ", e)
    refresh()

    return time.monotonic()

def list_splash(_settings=False):
    direction = varinit.text[9]
    lastrow = 103 if int(varinit.settings["long"]) == -1 else 102
    extra_space = " " if int(varinit.settings["long"]) == -1 else ""
    if varinit.settings["direction"] == 1: direction = varinit.text[10]
    if varinit.settings["direction"] == 2: direction = varinit.text[11]
    varinit.text[5] = extra_space + direction
    if varinit.shared["startup"] == 1 or _settings:
        sysprint(extra_space + varinit.text[2], lastrow, _refresh=False)
        sysprint(varinit.text[3]+str(wifi.radio.ipv4_address), lastrow+1, _refresh=False)
    else:
        if int(varinit.settings["stations"]["1"]["offset"]):
            sysprint(str(dicts.language[settings["language"]]["display"]["hiding"]) + str(varinit.settings["stations"]["1"]["offset"]) + varinit.settings["mins"], 102, _refresh=False)
    sysprint(LOGO_CHAR+str(varinit.settings["stations"]["1"]["mystation"]), 100, _refresh=False)
    sysprint(varinit.text[5], 101, _refresh=True)

def update_screen():
    
    lastrow = 103 if int(varinit.settings["long"]) == -1 else 102
        
    if wifi.radio.connected == True: return
    renderstring("1. " + dicts.language[varinit.settings["language"]]["display"]["connect_to"], 100, shading=True, smallfont=True, _cls=topbottom)
    renderstring("1. ", 100, shading=True, smallfont=True, sys_msg="white")

    macid = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] # mac-id för hotspot
    renderstring(str(macid), 101, shading=True, smallfont=True)
    #renderstring("t-skylt" + id[-2:], 101, shading=True, smallfont=True)
    
    renderstring("2. " + dicts.language[varinit.settings["language"]]["display"]["go_to"], lastrow,shading=True, smallfont=True)
    
    renderstring("2. ", lastrow,shading=True, smallfont=True, sys_msg="white")
    
    renderstring("http://" + str(wifi.radio.ipv4_address_ap), lastrow+1,shading=True, smallfont=True, _refresh=True)

def savesettings(_settings=varinit.settings, saved=dicts.language[varinit.settings["language"]]["display"]["saving"]):
    varinit.group.hidden = True; refresh()
    try:
        with open("settings.txt", "w") as f:
            f.write(json.dumps(_settings))
        print("Saved!")
    except: saved = "Read only"
    varinit.group.hidden = False; refresh()
    sysprint(saved, 0, color="red", shading=True, _refresh=True, ontop=True)
    reset_scroll(_delay=0.5)

try: 
    import font_mini
    dicts.font_mini = font_mini
    varinit.fonts.append(font_mini.font_mini)
    #print(len(varinit.fonts))
except:
    print("Not imported: font_mini")
    print("Attempting download...")
