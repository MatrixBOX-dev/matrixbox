from  varinit import *
from functions import *
import web
#from code import exit

def timer():
    html = web.timer(varinit.settings["language"], varinit.settings["timer"])
    return html

def mkhtml(checknet=0, version_message=False, reset_message=0):
    num = varinit.screen_selector
    varinit.reset_timer = time.monotonic()
    checknet = 1 if not functions.wifi.radio.connected else checknet
    varinit.checknet = checknet
    if version_message:
        varinit.version_msg = version_message

    if checknet and not varinit.saving_state:
        functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["select_network"], 10, cls=topbottom, shading=True)
        functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["save"], 11, shading=False)

    if reset_message:
        functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["reboot"], 10, cls=topbottom)
        varinit.shared["loop_counter"] = -7

    varinit.netlist = functions.scan() if checknet > 0 else []

    if varinit.newstation:
        s = varinit.datadict[varinit.newstation]
        varinit.settings["stations"][num]["siteid"] = varinit.newstation
        varinit.settings["stations"][num]["mystation"] = s[0:15]

    h = web.html()
    varinit.html_cache = h
    return h

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------

@ampule.route("/favicon.ico")
def favicon(request):
    return (404, {}, "")

@ampule.route("/", method="POST")
def huvudsidan(request):
    import ipaddress
    functions.reset_scroll()
    print("Posted")
    pairs = request.body.split('&')
    parsed_data = {}
    for pair in pairs:
        key, value = pair.split('=')
        parsed_data[key] = value
    request.params = parsed_data
    print(parsed_data)
    
    functions.nightcheck(force = True)
    settings_output_one = ""
    settings_output_two = ""
    data = ""
    varinit.results = ""
    
    if not request.params: varinit.saving_state = False
    else:
        settings_output_one = dicts.language[varinit.settings["language"]]["display"]["saving"]
        num = varinit.screen_selector
        try: varinit.settings["stations"][num]["buses_option"] = "1" if "option2" in request.params["buses_option"] else "0"
        except: varinit.settings["stations"][num]["buses_option"] = varinit.settings["stations"][num]["buses_option"]
        
        varinit.shared["startup"] = 2
        
        try:
            if request.params["sstring"] == "":
                varinit.settings["stations"][num]["mystation"] = varinit.settings["stations"][num]["mystation"].split('(')[0]
                varinit.shared["loop_counter"] = -3
            else:
                
                varinit.shared["startup"] = 0
                settings_output_one = dicts.language[varinit.settings["language"]]["display"]["searching"]
                settings_output_two = str(request.params["sstring"].replace("+"," "))
                for a in varinit.html_decode:
                    settings_output_two = settings_output_two.replace(a, varinit.html_decode[a])
                settings_output_two = settings_output_two[:20]
                datalist = []
                #datastr = ""
                datastr = """<option value=""" + "\"" + "0" +  "\"" + """>""" + varinit.dicts.language[varinit.settings["language"]]["display"]["select_station"] + """</option>"""

                data  = functions.fetch_data("data.t-skylt.se", 90, "/search_stop?country=" + varinit.settings["stations"][num]["country"] + "&operator=" + varinit.settings["stations"][num]["operator"] + "&station=" + request.params["sstring"])
                data = json.loads(data)                  
                try:
                    for stations in data:
                        datalist.append((stations, data[stations]))
                    datalist = sorted(datalist, key=lambda x: x[0])
                    for a in datalist:
                        name = str(a[0])
                        siteid = str(a[1])
                        varinit.datadict[siteid] = name
                        datastr += """<option value=""" + "\"" + siteid +  "\"" + """>""" + name + """</option>"""
                    try: 
                        varinit.settings["siteid"] = "000"
                        print(varinit.settings)
                    except Exception as e:
                        print(e)
                    #returndata = str(datalist)
                    
                except:
                    print("Error")
                    return (200, {}, mkhtml(0))
                
                varinit.currentfont = 1
                functions.sysprint(settings_output_one,10, cls=topbottom)
                functions.sysprint(settings_output_two,11)
                functions.refresh()
                time.sleep(0.1)  
            varinit.results = datastr
        except: pass
    
    print("Generating HTML:")
    __html = mkhtml(0)
    varinit.html_cache = __html
    functions.reset_scroll()
    varinit.saving_state = False
    return (200, {}, __html)

 



# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# --------------------------------- DEBUG FUNKTIONER ---- -----------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
  
   

@ampule.route("/", method="GET")
def huvudsidan(request):
    print(request.params)
    num = varinit.screen_selector
    """if "update" in request.params:
        try: microcontroller.cpu.frequency = 240000000
        except: pass
                                             
        functions.nightcheck(force = True)
        varinit.currentfont = 1
        
        functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["checking_update"],10, color="red", cls=topbottom, shading=True)
        functions.refresh()
        current_ver = varinit.settings["version"]
        try: 
            # ----------------------------------
            for i in range(10):
                try:
                    ver_txt = json.loads(functions.fetch_data(host="t-skylt.se", port=80, args="/update/ver.txt",filetype="text"))
                    print(ver_txt)
                except: 
                    print("Trying again", i)
                    continue
                break
            # ----------------------------------
        except Exception as errnum: 
            return (200, {}, mkhtml(0, "(x01) " + varinit.dicts.language[varinit.settings["language"]]["display"]["error"] + str(errnum)))
        except: 
            return (200, {}, mkhtml(0, "(x02) " + + varinit.dicts.language[varinit.settings["language"]]["display"]["error"]))
        
        files = ver_txt["files"]
        new_ver = ver_txt["ver"]
        version_message = "v. " + ver_txt["ver"] + ": " + varinit.dicts.language[varinit.settings["language"]]["display"]["no_update"]
        print(new_ver, current_ver)
        print(files)
        
        if new_ver > current_ver:
            functions.sysprint(varinit.dicts.language[varinit.settings["language"]]["display"]["dont_turn_off"],11)
            functions.refresh()
            time.sleep(1)
            
            functions.cls(topbottom)
            functions.refresh()
            total_files = len(files)
            cpver = ""
            if varinit.cpver == 9: cpver = "9/"
            try: varinit.socket_timeout = 60
            except: pass
            for filenum, file in enumerate(files):
                print(file)
                try:
                    wtype = "w"
                    ftype = "text"
                    
                    if "mpy" in file: 
                        wtype = "wb"
                        ftype = "binary"
                    try: 
                        varinit.wd()
                        print("Feeding timer")
                    except: print("Could not feed timer")
                    data = functions.fetch_data(host="t-skylt.se", port=80, args="/update/" + cpver + file, filetype=ftype)
                    ###################################
                    if len(data) < 100: break
                    ###################################
                    functions.cls(topbottom)
                    functions.refresh()    
                    try: 
                        with open(file, wtype) as p:
                            p.write(data)
                            print(dicts.language[varinit.settings["language"]]["display"]["updating"], file)
                    except: pass
                    functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["updating_file"],10,cls=topbottom)
                    functions.sysprint("((((((((((((((" +str(filenum + 1) + " av " + str(total_files) ,11)
                    functions.refresh()
                    
                except Exception as errnum: 
                    return (200, {}, mkhtml(0, dicts.language[varinit.settings["language"]]["display"]["try_again"] + str(errnum)))
                except: 
                    return (200, {}, mkhtml(0, dicts.language[varinit.settings["language"]]["display"]["try_again"]))
            varinit.shared["loop_counter"] = -7
            varinit.tg2.x = -1000
            
            version_message = dicts.language[varinit.settings["language"]]["display"]["new_version"] + str(new_ver)
            varinit.shared["loop_counter"] == -7
            functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["new_version"] + str(new_ver),10,cls=topbottom)
            functions.refresh()
            time.sleep(1)
            
            try:
                varinit.settings["version"] = str(new_ver)
                functions.savesettings()
            except: print("Could not save new version number in settings.txt")
            rm = 1
        else:
            functions.sysprint(dicts.language[varinit.settings["language"]]["display"]["no_update"],11)
            functions.refresh()
            time.sleep(1)
            
            rm = 0
        return (200, {}, mkhtml(0, version_message, reset_message = rm))"""



    # early exit for bot/prefetch requests
    try: 
        if "Dalvik" in request.headers["user-agent"]: return (204, {}, "")
    except: pass
    try: 
        if "prefetch" in request.headers["purpose"]: return (204, {}, "")
    except: pass

    html_decode = dicts.html_decode

    if "set_timer" in request.params:
        #print(request.params["set_timer"])
        _split = request.params["start"].split("to%3D")
        start = _split[0].replace("%3A", ":")
        end = _split[1].replace("%3A", ":")
        #if functions.check_correct_time(start, end): varinit.settings["timer"][request.params["set_timer"]] = [start, end]
        varinit.settings["timer"][request.params["set_timer"]] = [start, end]
        
        return (200, {}, "")
    
    elif "cleartimer" in request.params: 
        for i in varinit.settings["timer"]:
            varinit.settings["timer"][i] = ["00:00", "00:00"]

        #varinit.settings["timer"] = dicts.settingstxt["timer"]
        print("Timer reset!")
        return (200, {}, mkhtml())
    
    elif "timer" in request.params: 
        varinit.currentfont = 1
        return (200, {}, timer())
    elif "width" in request.params:
        
        if request.params["width"] == "xs": varinit.settings["long"] = -1
        elif request.params["width"] == "x": varinit.settings["long"] = 0
        elif request.params["width"] == "xl": varinit.settings["long"] = 1
        else: return (200, {}, mkhtml())
        functions.savesettings()
        functions.reset()
        return (200, {}, mkhtml())

    elif "checknet" in request.params: 
        varinit.currentfont = 1
        return (200, {}, mkhtml(1))
    elif "language" in request.params: 
        varinit.settings["language"] = request.params["language"]
        varinit.text = functions.load_text()
        varinit.html_cache = mkhtml(0)
        return (200, {}, varinit.html_cache)
    elif "operator" in request.params:
        varinit.results = ""
        stn = varinit.settings["stations"][num]
        stn["siteid"] = "0"
        stn["operator"] = request.params["operator"].lower()
        if "country" in request.params:
            stn["country"] = request.params["country"].lower()
        return (200, {}, "")
    elif "change_screen" in request.params:
        print(request.params["change_screen"])
        varinit.screen_selector = request.params["change_screen"]
        return (200, {}, "")
        
    elif "country" in request.params:
        varinit.results = ""
        varinit.settings["stations"][num]["siteid"] = "0"
        varinit.settings["stations"][num]["operator"] = ""
        
        if request.params["country"].lower() == "no":
            varinit.settings["stations"][num]["operator"] = "no"
            varinit.settings["stations"][num]["siteid"] = "0"
        if request.params["country"].lower() == "dk":
            varinit.settings["stations"][num]["operator"] = "dk"
            varinit.settings["stations"][num]["siteid"] = "0"
        
        varinit.settings["stations"][num]["country"] = request.params["country"].lower()
        return (200, {}, "")
    elif "full_page" in request.params:
        #varinit.settings["siteid"] = "00"
        return (200, {}, json.dumps("<b>XUZ</b>"))
    
    elif "newstation" in request.params: 
        try: 
            station_decoded = str(request.params["newstation"])
            for a in varinit.html_decode:
                station_decoded = station_decoded.replace(a, varinit.html_decode[a])
            varinit.settings["stations"][num]["mystation"] = str(varinit.datadict[station_decoded]).split(",")[0].split("(")[0]
        except: pass
        print("New: ------ ", request.params["newstation"])
        functions.cls(topbottom), functions.cls(top), functions.cls(bottom)
        functions.sysprint("% "+ varinit.settings["stations"][num]["mystation"],0, _refresh=True, ontop=True)
        try: varinit.settings["stations"][num]["siteid"] = request.params["newstation"]
        except: pass
        functions.reset_scroll(_delay=1)
        return (200, {}, "")
    
    elif "ssid" in request.params:
        varinit.settings["ssid"] = request.params["ssid"]
        for a in html_decode:
            varinit.settings["ssid"] = varinit.settings["ssid"].replace(a, html_decode[a])
        return (200, {}, "")
    elif "user" in request.params:
        varinit.settings["user"] = request.params["user"]
        for a in html_decode:
            varinit.settings["user"] = varinit.settings["user"].replace(a, html_decode[a])
        return (200, {}, "")
    elif "password" in request.params:
        varinit.settings["password"] = request.params["password"]
        for a in html_decode:
            varinit.settings["password"] = varinit.settings["password"].replace(a, html_decode[a])
        #functions.sysprint(str(dicts.language[varinit.settings["language"]]["display"]["connecting"]),10,cls=topbottom)
        #functions.sysprint(str(varinit.settings["ssid"]),11, _refresh=True, _delay=1)
        return (200, {}, "")
    elif "connect_wifi" in request.params:
        functions.sysprint(str(dicts.language[varinit.settings["language"]]["display"]["connecting"]),10,cls=topbottom)
        functions.sysprint(str(varinit.settings["ssid"]),11, _refresh=True, _delay=1)
        functions.wifiattempt()
        if functions.wifi.radio.connected == True: functions.savesettings()
        x = json.dumps(functions.wifi.radio.connected)
        return (200, {}, x)
    elif "save" in request.params:
        functions.savesettings()
        x = json.dumps(functions.wifi.radio.connected)
        return (200, {}, x)
    elif "show_msgs" in request.params:
        varinit.settings["show_msgs"] = 1 - varinit.settings["show_msgs"]
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "sleep" in request.params:
        varinit.settings["sleep"] = 1 - varinit.settings["sleep"]
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "button_mode" in request.params:
        varinit.settings["button_mode"] = 1 - int(varinit.settings.get("button_mode", 0))
        return (200, {}, "")
    elif "show_station" in request.params:
        varinit.settings["show_my_station"] = 1 - varinit.settings["show_my_station"]
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "buses_option" in request.params:
        varinit.settings["stations"][num]["buses_option"] = request.params["buses_option"]
        varinit.use_cached_data = True
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "type" in request.params:
        varinit.settings["stations"][num][request.params["type"].upper()] = 1 - int(varinit.settings["stations"][num][request.params["type"].upper()])
        varinit.use_cached_data = True
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "line" in request.params:
        varinit.settings["stations"][num][request.params["line"]] = 1 - int(varinit.settings["stations"][num][request.params["line"]])
        varinit.use_cached_data = True
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "maxdest" in request.params:
        varinit.settings["maxdest"] = int(request.params["maxdest"])
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "direction" in request.params:
        varinit.settings["stations"][num]["direction"] = int(request.params["direction"])
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "multiple" in request.params:
        varinit.settings["multiple"] = 1 - varinit.settings["multiple"]
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "screen" in request.params:
        varinit.screen_selector = request.params["screen"]
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "offset" in request.params:
        varinit.settings["stations"][num]["offset"] = int(request.params["offset"])
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "brightness" in request.params:
        varinit.settings["brightness"] = int(request.params["brightness"])
        functions.colors()
        if int(varinit.settings["listmode"]): functions.switch(_screen=False)
        return (200, {}, "")
    elif "scroll" in request.params:
        varinit.settings["scroll"] = int(request.params["scroll"])
        return (200, {}, "")
    elif "startTime" in request.params:
        print(request.params)
        print(varinit.settings["timer"])
        varinit.settings["timer"][request.params["weekday"]] = {"start":request.params["startTime"], "end":request.params["endTime"]}
        print(varinit.settings["timer"])
        return (200, {}, mkhtml())
    elif "onoff" in request.params:
        varinit.on_off_counter = 1 - varinit.on_off_counter
        functions.nightcheck()
        functions.refresh()
        return (200, {}, "")
    elif "color" in request.params: 
        varinit.settings["color"] = int(request.params["color"])
        functions.colors()
        if int(varinit.settings["listmode"]): functions.switch(_screen=False)
        return (200, {}, "")
    elif "listmode" in request.params: 
        if varinit.display.width > 64 and varinit.display.height <= 32:
            varinit.settings["listmode"] = 1 - int(varinit.settings["listmode"])
        functions.switch(_screen = True)
        return (200, {}, "")
    elif "clocktime" in request.params: 
        varinit.settings["clocktime"] = 1 - varinit.settings["clocktime"]
        functions.switch(_screen = False)
        return (200, {}, "")
    elif "listcolor_time" in request.params:
        varinit.settings["listcolor_time"] = 1 - int(varinit.settings.get("listcolor_time", 0))
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "listcolor" in request.params: 
        varinit.settings["listcolor"] = 1 - int(varinit.settings["listcolor"])
        functions.colors()
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "font_size" in request.params:
        fs = request.params.get("font_size", "small")
        varinit.settings["mini"] = 1 if fs == "mini" else 0
        varinit.settings["large_list"] = 1 if fs == "large" else 0
        functions.colors()
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "xs_line_id" in request.params: 
        varinit.settings["xs_line_id"] = 1 - int(varinit.settings.get("xs_line_id", 0))
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "dest_scroll" in request.params:
        varinit.settings["dest_scroll"] = 1 - int(varinit.settings.get("dest_scroll", 0))
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "invert" in request.params: 
        varinit.settings["invert"] = 1 - int(varinit.settings["invert"])
        functions.colors()
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "strip_dest" in request.params:
        try:
            strip_dest = []
            parts = request.params["strip_dest"].replace("%20", " ")
            for part in parts.split(","):
                part = part.strip()
                if part: strip_dest.append(part)
            varinit.settings["strip_dest"] = strip_dest
            functions.switch(_screen=False)
        except Exception as e:
            print(e)
        return (200, {}, "")
    elif "show_lines" in request.params:
        try:
            show_lines = []
            lines = request.params["show_lines"].replace("%20", "")
            for line in lines.split(","):
                show_lines.append(line)
            varinit.settings["show_lines"] = show_lines
            functions.switch(_screen=False)
        except Exception as e: 
            print(e)
        return (200, {}, "")
    elif "line_length" in request.params:
        if int(request.params["line_length"]) > -1 and int(request.params["line_length"]) < 9:
            varinit.settings["line_length"] = int(request.params["line_length"])
            functions.switch(_screen=False)
        return (200, {}, "")
    elif "no_more_departures" in request.params:
        if request.params["no_more_departures"] == "": varinit.settings["no_more_departures"] = dicts.language[settings["language"]]["display"]["no_more_departures"]
        else: varinit.settings["no_more_departures"] = str(request.params["no_more_departures"])
        for a in html_decode:
            varinit.settings["no_more_departures"] = varinit.settings["no_more_departures"].replace(a, html_decode[a])
        varinit.text = functions.load_text()
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "mins" in request.params:
        if request.params["mins"] == "": varinit.settings["mins"] = " min"
        else: varinit.settings["mins"] = str(request.params["mins"])
        for a in html_decode:
            varinit.settings["mins"] = varinit.settings["mins"].replace(a, html_decode[a])
        functions.switch(_screen=False)
        return (200, {}, "")
    elif "power" in request.params:
        if int(request.params["power"]) > 6 and int(request.params["power"]) < 21:
            varinit.settings["power"] = int(request.params["power"])
            wifi.radio.tx_power = varinit.settings["power"]
        return (200, {}, "")
    elif "rotate" in request.params:
        current = varinit.display.rotation
        new_r = (current + 90) % 360
        varinit.display.rotation = new_r
        varinit.settings["rotation"] = new_r
        varinit.if_long = varinit.display.width
        varinit.if_tall = varinit.display.height
        varinit.rotated = new_r in (90, 270)
        if varinit.rotated:
            varinit.settings["listmode"] = 1
        functions.colors()
        functions.switch(force=True)
        return (200, {}, "")
    elif "rt_indicator" in request.params: 
        varinit.settings["rt_indicator"] = 1 - int(varinit.settings["rt_indicator"])
        if int(varinit.settings["listmode"]): functions.switch(_screen=False)
        return (200, {}, "")
    
    if functions.wifi.radio.connected == True: functions.reset_scroll()
    print("mkhtml 0")
    #return (200, {}, mkhtml(0))
    if varinit.html_cache and functions.wifi.radio.connected == False:
        print("Using cached HTML")
        return (200, {}, varinit.html_cache)
    else: 
        print("Generating new HTML")
        varinit.html_cache = mkhtml(0)
        return (200, {}, varinit.html_cache)
        

@ampule.route("/checknet")
def checknet_route(request):
    varinit.checknet = 1
    netlist = functions.scan()
    varinit.netlist = netlist
    opts = "<option value='" + str(varinit.settings["ssid"]) + "' selected>" + str(varinit.settings["ssid"]) + "</option>"
    for n in netlist:
        ns = str(n)
        opts += "<option value='" + ns + "'>" + ns + "</option>"
    return (200, {}, opts)

@ampule.route("/search")
def search_station(request):
    num = varinit.screen_selector
    sstring = request.params.get("sstring", "") if hasattr(request.params, 'get') else ""
    if not sstring:
        try: sstring = request.params["sstring"]
        except: return (200, {}, "")
    datastr = '<option value="0">' + varinit.dicts.language[varinit.settings["language"]]["display"]["select_station"] + '</option>'
    try:
        data = functions.fetch_data("data.t-skylt.se", 90, "/search_stop?country=" + varinit.settings["stations"][num]["country"] + "&operator=" + varinit.settings["stations"][num]["operator"] + "&station=" + sstring)
        data = json.loads(data)
        datalist = []
        for stations in data:
            datalist.append((stations, data[stations]))
        datalist = sorted(datalist, key=lambda x: x[0])
        for a in datalist:
            name = str(a[0])
            siteid = str(a[1])
            varinit.datadict[siteid] = name
            datastr += '<option value="' + siteid + '">' + name + '</option>'
    except Exception as e:
        print("Search error:", e)
    varinit.results = datastr
    return (200, {}, datastr)

@ampule.route("/setdns")
def _dns(request):
    print("================== DNS ==================")
    print(request.params)
    try:
        if request.params["clear"] == "true":
            import os
            os.remove("no_dhcp")
            print("Flushed manual DHCP settings")
    except Exception as e:
        print("FLUSHING IP: Read only!! + ", e)
    
    functions.reset()
    return (200, {}, mkhtml())
    
@ampule.route("/dns")
def enable_dns(request):
    varinit.dns = True
    return (200, {}, mkhtml())



@ampule.route("/setdns", method="POST")
def _dns_save(request):
    print("================== DNS / POST ==================")
    import ipaddress
    pairs = request.body.split('&')
    parsed_data = {}
    for pair in pairs:
        key, value = pair.split('=')
        parsed_data[key] = value
    request.params = parsed_data
    print(request.params)
    
    functions.cls(topbottom)
    functions.refresh()
    try:
        with open("no_dhcp", "w") as f:
            f.write(json.dumps(request.params))
    except Exception as e:
        print("SETTINGS IP: Read only + ", e)
    functions.wifiattempt()
    return (200, {}, mkhtml())
 
 




@ampule.route("/cmd", method="GET")
def _cmd(request):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Console and Command</title>
    <style>
        ...
    </style>
</head>
<body>
    <div id="console-output"></div>
    <input id="command-input" type="text" placeholder="Enter command...">
    <button id="command-button">Execute</button>
<script>
    let outputConsole = document.getElementById('console-output');
    let commandInput = document.getElementById('command-input');
    let commandButton = document.getElementById('command-button');

    console.log('JavaScript is running...');

    commandButton.addEventListener('click', async () => {
        console.log('Button clicked...');
        let command = commandInput.value;
        console.log('Command:', command);

        if (command) {
            console.log('Sending command to server...');
            const endpoint = 'cmd';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Command': command,
                    },
                    body: null,
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                console.log('Response from server:', data);

                outputConsole.innerHTML += `${command}\n`;
            } catch (error) {
                console.error('Error sending command:', error);
            }
        }
    });
</script>
</body>
</html>"""
    return (200, {}, html)

@ampule.route('/cmd', method='POST')
def execute_command(request):
    command = request.headers["x-command"]
    _c = str(command)
    _e = ""
    try:
        exec(command)
    except Exception as e:
        _e = str(e)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Console and Command</title>
    <style>
        ...
    </style>
</head>
<body>
""" + e + """<br>""" + _c + """
    <div id="console-output"></div>
    <input id="command-input" type="text" placeholder="Enter command...">
    <button id="command-button">Execute</button>
<script>
    let outputConsole = document.getElementById('console-output');
    let commandInput = document.getElementById('command-input');
    let commandButton = document.getElementById('command-button');

    console.log('JavaScript is running...');

    commandButton.addEventListener('click', async () => {
        console.log('Button clicked...');
        let command = commandInput.value;
        console.log('Command:', command);

        if (command) {
            console.log('Sending command to server...');
            const endpoint = 'cmd';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Command': command,
                    },
                    body: null,
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                console.log('Response from server:', data);

                outputConsole.innerHTML += `${command}\n`;
            } catch (error) {
                console.error('Error sending command:', error);
            }
        }
    });
</script>
</body>
</html>"""    
    
    return (200, {}, html)

@ampule.route('/settings')
def _settings(request):
    return (200, {}, str(varinit.settings))

@ampule.route('/generate_204')
def _android(request):
    print(varinit.settings)
    return (204, {}, "")

@ampule.route('/check_network_status')
def _check_network_status(request):
    x = json.dumps(functions.wifi.radio.connected)
    print(x)
    return (200, {}, x)

@ampule.route('/invert')
def _invert(request):
    varinit.settings["invert"] = 1 - int(varinit.settings["invert"])
    functions.colors()
    functions.switch(_screen=False)
    return (200, {}, "")

@ampule.route('/debug')
def _debug(request):
    try: varinit.settings["debug"] = 1 - varinit.settings["debug"]
    except: varinit.settings["debug"] = 1
    return (200, {}, "Debugmode: " + str(varinit.settings["debug"]))

@ampule.route('/ping')
def _ping_graph(request):
    varinit.ping = 1 - varinit.ping
    if not varinit.ping: return  (200, {}, mkhtml())
    while varinit.ping:
        if functions.ping_screen(): break
    return (200, {}, mkhtml())






@ampule.route("/exit", method="GET")
def webinterface(request):
    varinit.exit = True
    #functions.reset()
    #print(varinit.exit)
#   varinit.exit = True
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")
