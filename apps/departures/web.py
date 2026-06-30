css = ""
try: from css import _css as css
except: pass
from dicts import language, flag as _flag_img, country_name

country_and_operators = {
  "se":[["sl","SL (Stockholm)"],["vt","VT (Västtrafik)"],["otraf","Östgötatrafiken"],["vastmanland","VL (Västmanlands län)"],["dt","DT (Dalatrafik)"],["jlt","JLT (Jönköpings län)"],["krono","KRONO (Kronobergs länstrafik)"],["ul","UL (Uppsala län)"],["klt","KLT (Kalmar länstrafik)"],["orebro","Länstrafiken Örebro"],["xt","X-Trafik (Gävleborg)"],["varm","Värmlandstrafik - Karlstadsbuss"],["skane","Skånetrafiken"],["norrbotten","Norrbotten"],["fe","Trafikverkets färjor"],["sj","SJ (Trafikverket)"]],
  "dk":[["kb","Scheduled"],["dk_rt","Real-time (experimental)"]],
  "lu":[["all","All of Luxembourg"]],
  "no":[["no","Entur (entire Norway)"]],
  "fi":[["all","All of Finland"], ["hsl","HSL"]],
  "cr":[["za","ZET (Zagreb)"]],
  "nl":[["all","Countrywide"], ["ns","Nederlandse Spoorwegen"]],
  "ch":[["ch","Switzerland"],["sbb","SBB"]],
  "fr":[["sncf","SNCF"], ["pa","Paris"], ["ilevia","Ilévia"], ["met","Le MET"]],
  "lt":[["vil","Vilnius"]],
  "be":[["sncb","SNCB"], ["stib","STIB"], ["delijn","De Lijn"]],
  "uk":[["lo","Tfl (London)"]],
  "hu":[["bu","Budapest"]],
  "cz":[["pr","Prague (PID)"]],
  "it":[["ro","Rome"]],
  "pt":[["carris","Carris"]],
  "pl":[["wa","Warsaw"],["kr","Krakow"],["wa_tram","Warszawa Tram"],["plk","PLK"]],
  "at":[["wl","Vienna"]],
  "es":[["barcelona","Barcelona (AMB)"]],
  "ie":[["all","All real-time operators"]],
  "de":[["local","Germany (gtfs.de)"],["db_trains","DB-trains (Deutsche Bahn)"],["be","Berlin (Unofficial API)"],["vbb","VBB/BVG (Berlin-Brandenburg)"],["vrr","VRR (Rhein-Ruhr)"],["kvv","KVV (Karlsruhe)"],["rmv","RMV (Frankfurt)"],["hochbahn","HVV (Hamburg etc.)"],["vrn","VRN (Rhein-Neckar)"],["vbn","VBN (Bremen-Niedersachsen)"],["vvo","VVO (Dresden)"]]
}

def _opt(val, cur, label):
    s = " selected" if str(val) == str(cur) else ""
    return "<option value='" + str(val) + "'" + s + ">" + label + "</option>"


def _chk(name, val, url, label):
    c = " checked" if int(val) else ""
    return '<label class="sw"><input type="checkbox" id="' + name + '" data-u="' + url + '"' + c + '><span>' + label + '</span></label>'


PAGE_TPL = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">
<link href="data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAA/SURBVDhPY2RgYPgPxGQDsAFAAOGRCBgZGREGgDikAJgeJiifbDDwBuAMRPQwwaVmGITBqAHUykwQLjmAgQEA3oYYFR16cP8AAAAASUVORK5CYII=" rel="icon" type="image/x-icon"/>
<title>{TITLE}</title><style>{CSS}@keyframes guide-pulse{0%,100%{box-shadow:0 0 0 0 rgba(220,220,255,0)}60%{box-shadow:0 0 0 5px rgba(200,200,255,.3)}}</style></head><body>
<div class="container">
<div style="text-align:right"><a href="/exit" style="color:#ff4444;text-decoration:none;font-size:20px">&#x274C;</a></div>
<div class="card" style="text-align:center">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem"><div id="network">{CONN_STATUS}</div><input type="checkbox" id="onoff" class="l" data-u="/?onoff=active" {ONOFF_CHK}></div>
<div class="sh">{HEADER}</div>
<div style="margin-top:.3rem;font-size:.7rem;color:#aaa">{VERSION_TEXT}</div></div>
<div class="card"><small><b>{T_INFO}</b> {IP_DISPLAY}<br>{INSTR_TEXT}</small></div>
<form method="post" action="/">
<div class="card"><div class="form-row"><div class="col">
<label for="ssid"><a href="#" onclick="doScan();return false">&#128268;</a> {T_NETWORK}</label>
<select id="ssid" class="form-control" name="ssid" data-p="ssid" data-e="change" {NET_DIS}>{SSID_OPTIONS}</select>
</div><div class="col"><label for="password">{T_PASSWORD}</label>
<input type="text" id="password" class="form-control" name="password" placeholder="*******" data-p="password" data-e="blur" data-enc="1" {NET_DIS}>
<div style="text-align:right;margin-top:.5rem">
<button type="button" class="btn btn-outline-secondary btn-sm" id="connect_wifi" data-u="/?connect_wifi=true" data-net="1" {NET_DIS}>{T_CONNECT}</button>
</div></div></div></div>
<div class="card">
<div class="form-row" style="margin-bottom:.5rem"><div class="col" style="flex:0 0 auto">
<div style="display:flex;align-items:center;gap:.4rem">
<div class="dropdown"><button type="button" class="dropbtn" id="opbtn" {OPBTN_PULSE}>{COUNTRY_FLAG} {OPERATOR} &#9660;</button>
<div class="dropdown-content">{COMBINED_LIST}</div></div>
<div id="screenbtns" style="{SCREEN_BTN_DISP}">{SCREEN_BUTTONS}</div>
</div>
</div><div class="col">
<select id="newstation" class="form-control" name="newstation" data-p="newstation" data-e="change" {RESULT_DIS} {RESULT_STYLE} onchange="this.style.animation=''">{RESULTS}</select>
</div></div>
<div class="form-row" style="margin-bottom:.5rem"><div class="col">
<input type="text" id="sstring" class="form-control" name="sstring" placeholder="{STATION_PH}" {SEARCH_DIS} {SSTRING_PULSE} onkeydown="if(event.key==='Enter'){event.preventDefault();doSearch()}">
</div><div class="col" style="flex:0 0 auto;display:flex;align-items:center">
<button type="button" class="btn btn-outline-secondary btn-sm" id="searchbtn" onclick="doSearch()" {SEARCH_DIS}>{T_SEARCH}</button>
</div></div></div>
<div class="card">
<div class="grp"><div class="grp-title">&#9881; {SCROLL_LABEL} / {T_NO_DEPARTURES}</div>
<div class="form-row">{SCROLL_SECTION}<div class="col">
<label for="maxdest">{T_NO_DEPARTURES}</label>
<select id="maxdest" name="maxdest" class="form-control" data-p="maxdest" data-e="change">{MAXDEST_OPTIONS}</select>
</div></div></div>
<div class="grp"><div class="grp-title">&#128336; {T_HIDE_DEPARTURES} / {DIRECTION_LABEL}</div>
<div class="form-row"><div class="col">
<label for="offset">{T_HIDE_DEPARTURES}</label>
<select id="offset" name="offset" class="form-control" data-p="offset" data-e="change">{OFFSET_OPTIONS}</select>
</div><div class="col">{DIRECTION_SECTION}</div></div></div>
<div class="grp"><div class="grp-title">&#128651; {T_TRAFFIC_TYPES}</div>
<div class="tt-col">
{METRO_SECTION}
{BUS_SECTION}
{TRAIN_CHK}
{TRAM_SECTION}
{SHIP_SECTION}
</div>
<div style="margin-top:.4rem">{SL_COLORS}{SL_BUS_OPTIONS}</div>
</div></div>
<div class="card">
{LISTMODE_CHK}
{CLOCKTIME_CHK}
{MULTIPLE_SECTION}
{DEVIATIONS_SECTION}
{SLEEP_CHK}
{BUTTON_MODE_CHK}
{SHOW_STATION_CHK}
</div>
<div style="margin-bottom:.6rem">
<button type="button" class="save-btn" data-u="/?save=true">&#128190; {T_SAVE}</button></div>
<div class="card"><label for="user">{T_USER}</label>
<input type="text" id="user" class="form-control" name="user" placeholder="{USER_PH}" data-p="user" data-e="change" data-enc="1"></div>
<div class="card"><details>
<summary>&#9881; {T_ADVANCED}</summary>
<div class="sh" style="margin:.75rem 0">{T_ADVANCED_SETTINGS}</div>
<table>
<tr><td><b>{T_TEMP}</b></td><td>{TEMP_VAL}&#176;C</td></tr>
<tr><td><b>Uptime</b></td><td>{UPTIME_VAL} {T_MINUTES}</td></tr>

<tr><td><b>{T_SYSTEM_LANGUAGE}</b></td><td>
<div class="dropdown"><button class="dropbtn" disabled>{LANG}</button>
<div class="dropdown-content">
<a href="#" onclick="fetch('/?language=se');this.closest('.dropbtn').textContent='se';return false">Svenska</a>
<a href="#" onclick="fetch('/?language=en');this.closest('.dropbtn').textContent='en';return false">English</a>
</div></div></td></tr>
<tr><td><b>{T_TONE}</b></td><td>
<button style="background:#e09d00;color:#fff;border-color:#e09d00" type="button" data-u="/?color=0">{T_ORANGE}</button>
<button style="background:#f5d105;color:#111;border-color:#f5d105" type="button" data-u="/?color=1">{T_YELLOW}</button>
{WHITE_BTN}</td></tr>
<tr><td><b>{T_LIST_COLORS}</b></td><td>{LISTCOLOR_CHK} {LISTCOLOR_TIME_CHK}</td></tr>
{FONT_SIZE_ROW}
{XS_LINE_ID_ROW}
<tr><td><b>Scroll dest</b></td><td>{DEST_SCROLL_CHK}</td></tr>
<tr><td><b>Timer</b></td><td><button type="button" onclick="location.href='/?timer=set'">&#8987;</button></td></tr>
<tr><td><b>{T_ROTATION}</b></td><td><button type="button" data-u="/?rotate=1">&#128260; 90&deg;</button></td></tr>
<tr><td><b>{T_RT_INDICATOR}</b></td><td>{RT_INDICATOR_CHK}</td></tr>
<tr><td><b>{T_POWER}</b></td><td><input type="text" id="power" class="form-control" style="width:80px;display:inline" placeholder="{POWER_VAL}" data-p="power" data-e="blur"></td></tr>
<tr><td><b>{T_LINE_LENGTH}</b></td><td><input type="text" id="line_length" class="form-control" style="width:80px;display:inline" placeholder="{LINE_LENGTH_VAL}" data-p="line_length" data-e="blur"></td></tr>
<tr><td><b>{T_SHOW_LINES}</b></td><td><input type="text" id="show_lines" class="form-control" style="width:160px;display:inline" placeholder="{SHOW_LINES_VAL}" data-p="show_lines" data-e="blur"></td></tr>
<tr><td><b>Strip from dest</b></td><td><input type="text" id="strip_dest" class="form-control" style="width:160px;display:inline" placeholder="{STRIP_DEST_VAL}" data-p="strip_dest" data-e="blur"></td></tr>
<tr><td><b>{T_NO_MORE_DEP}</b></td><td><input type="text" id="no_more_departures" class="form-control" style="width:160px;display:inline" placeholder="{NO_MORE_DEP_VAL}" data-p="no_more_departures" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>{T_MINS}</b></td><td><input type="text" id="mins" class="form-control" style="width:100px;display:inline" placeholder="{MINS_VAL}" data-p="mins" data-e="blur" data-enc="1"></td></tr>
</table>
{DNS_SECTION}
</details></div>
<div id="opsdata" style="display:none">{OPS_JSON}</div>
<div id="stndata" style="display:none">{STN_JSON}</div>
<script>
var OPS=JSON.parse(document.getElementById('opsdata').textContent);var STN=JSON.parse(document.getElementById('stndata').textContent);
function pickScr(n){fetch('/?screen='+n);var d=STN[n];if(!d)return;document.querySelectorAll('.scr-btn').forEach(function(b){b.classList.toggle('act',b.textContent==String(n));});var co=d.co,op=d.op.toLowerCase();var el=document.querySelector('.dd-grid img[data-c="'+co+'"]');var f=el?el.outerHTML.replace(/dd-sel/g,'')+' ':'';var nm=d.op.toUpperCase();var ops=OPS[co]||[];for(var i=0;i<ops.length;i++){if(ops[i][0]===op){nm=ops[i][1];break;}}document.getElementById('opbtn').innerHTML=f+nm+' &#9660;';document.getElementById('sstring').placeholder=d.ms||'';var cb={METRO:d.M,BUS:d.B,TRAIN:d.T,TRAM:d.R,SHIP:d.S,r:d.r,g:d.g,b:d.b};for(var k in cb){var e=document.getElementById(k);if(e)e.checked=!!cb[k];}var isSL=op==='sl';var sc=document.getElementById('slcolors');if(sc)sc.style.display=isSL?'':'none';var sb=document.getElementById('slbusopts');if(sb)sb.style.display=isSL?'':'none';var ab=document.getElementById('all_buses2');if(ab)ab.checked=!d.bo;var nb=document.getElementById('night_buses2');if(nb)nb.checked=!!d.bo;var of2=document.getElementById('offset');if(of2)of2.value=d.of;var di=document.getElementById('direction');if(di)di.value=d.di;}
function pickC(c){var d=document.getElementById('ddops');d.innerHTML='';var ops=OPS[c]||[];for(var i=0;i<ops.length;i++){var a=document.createElement('a');a.href='#';a.textContent=ops[i][1];(function(cc,code,name){a.onclick=function(e){e.preventDefault();chCO(cc,code,name);return false;};})(c,ops[i][0],ops[i][1]);d.appendChild(a);}document.querySelectorAll('.dd-grid img').forEach(function(im){im.classList.toggle('dd-sel',im.dataset.c===c);});}
function chCO(c,o,n){fetch('/?country='+c+'&operator='+o);var el=document.querySelector('.dd-grid img[data-c="'+c+'"');var f='';if(el)f=el.outerHTML.replace(/dd-sel/g,'')+' ';document.getElementById('opbtn').innerHTML=f+n+' &#9660;';document.getElementById('opbtn').style.animation='';document.getElementById('sstring').style.animation='guide-pulse 2.5s ease-in-out infinite';var sc=document.getElementById('slcolors');if(sc)sc.style.display=o==='sl'?'':'none';var sb=document.getElementById('slbusopts');if(sb)sb.style.display=o==='sl'?'':'none';}
function doSearch(){var s=document.getElementById('sstring').value;if(!s)return;var b=document.getElementById('searchbtn');b.disabled=true;b.innerHTML='<span class="spin"></span>';fetch('/search?sstring='+encodeURIComponent(s)).then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('newstation');sel.innerHTML=h;sel.disabled=false;sel.style.background='#2a1215';sel.style.borderColor='#dc3545';sel.style.animation='guide-pulse 2.5s ease-in-out infinite';document.getElementById('sstring').style.animation='';b.disabled=false;b.textContent='{T_SEARCH}';}).catch(function(){b.disabled=false;b.textContent='{T_SEARCH}';});}
function doScan(){fetch('/checknet').then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('ssid');sel.innerHTML=h;sel.disabled=false;document.getElementById('password').disabled=false;document.getElementById('connect_wifi').disabled=false;}).catch(function(){});}

var mc=document.getElementById('multiple');if(mc)mc.addEventListener('change',function(){var sb=document.getElementById('screenbtns');if(sb)sb.style.display=mc.checked?'':'none';});
function setFont(v,el){fetch('/?font_size='+v);var bs=el.parentNode.querySelectorAll('button');bs.forEach(function(b){b.style.background='transparent';b.style.color='#aaa';});el.style.background='#e09d00';el.style.color='#111';}
document.querySelectorAll('[data-u],[data-p]').forEach(function(el){
el.addEventListener(el.dataset.e||'click',function(ev){
var u=el.dataset.u;
if(!u){var v=ev.target.value.replace(/#/g,'%23');if(el.dataset.enc)v=encodeURIComponent(v);u='/?'+el.dataset.p+'='+v;}
var f=fetch(u,{method:'GET'});
if(el.dataset.net){f.then(function(r){return r.json()}).then(function(d){
var div=document.getElementById('network');
if(d===true)div.innerHTML='{CONN_OK}';
else if(d===false)div.innerHTML='{CONN_FAIL}';
else div.innerText='Error';
}).catch(function(){});}
});});
</script>
</form></div></body></html>"""

# Pre-split template at import time: list of (text_fragment, placeholder_key)
_PARTS = []
_tpl_pos = 0
_tpl_last = 0
while _tpl_pos < len(PAGE_TPL):
    _i = PAGE_TPL.find('{', _tpl_pos)
    if _i < 0: break
    _j = PAGE_TPL.find('}', _i + 1)
    if _j < 0: break
    _k = PAGE_TPL[_i+1:_j]
    _ok = len(_k) > 0
    if _ok:
        for _c in _k:
            if _c != '_' and not ('A' <= _c <= 'Z'):
                _ok = False
                break
    if _ok:
        _PARTS.append((PAGE_TPL[_tpl_last:_i], _k))
        _tpl_last = _j + 1
        _tpl_pos = _j + 1
    else:
        _tpl_pos = _i + 1
_PARTS.append((PAGE_TPL[_tpl_last:], ""))


def html():
    import varinit, functions, microcontroller, time
    num = varinit.screen_selector
    s = varinit.settings
    stn = s["stations"][num]
    lg = s["language"]
    T = language[lg]["settings"]
    D = language[lg]["display"]
    connected = functions.wifi.radio.connected
    op = stn["operator"].upper()
    if not op: op = T["operator"]
    co = stn["country"].lower()
    ip = str(functions.wifi.radio.ipv4_address) if connected else ""
    uptime = round((time.monotonic() - varinit.starttime) / 60)
    varinit.uptime = str(uptime)
    if_long = varinit.if_long

    # version button
    #vmsg = varinit.version_msg if varinit.version_msg else ("T-Skylt v. " + str(s["version"]))
    #if varinit.new_version_available: vmsg = "&#10071; " + vmsg
    vmsg = ""
    update_dis = "" if varinit.new_version_available else "disabled"

    # connection status
    if connected:
        conn = "<green_box><small>" + T["connected"] + "</small></green_box>"
    else:
        conn = "<red_box><small>" + T["not_connected"] + "</small></red_box>"
    conn_ok = ("<green_box><small>" + T["connected"] + "</small></green_box>").replace("'", "\\'")
    conn_fail = ("<red_box><small>" + T["not_connected"] + "</small></red_box>").replace("'", "\\'")

    # ssid options
    _p = ["<option value='", str(s["ssid"]), "' selected>", str(s["ssid"]), "</option>"]
    if hasattr(varinit, 'netlist'):
        for n in varinit.netlist:
            _ns = str(n)
            _p.append("<option value='")
            _p.append(_ns)
            _p.append("'>")
            _p.append(_ns)
            _p.append("</option>")
    ssid_opt = "".join(_p)

    # network disable
    if connected and not (hasattr(varinit, 'checknet') and varinit.checknet):
        net_dis = "disabled"
    else:
        net_dis = ""

    # country flag
    country_flag = _flag_img(co)

    # flag grid + operator data
    _p = ["<div class='dd-grid'>"]
    for c in country_and_operators:
        _p.append(_flag_img(c).replace("<img ", "<img onclick=\"pickC('" + c + "')\" data-c='" + c + "' "))
    _p.append("</div><div class='dd-ops' id='ddops'></div>")
    combined_list = "".join(_p)

    # operator data JSON for client-side
    import json
    ops_json = "".join(c if ord(c) < 128 else "\\u{:04x}".format(ord(c)) for c in json.dumps(country_and_operators))

    # station settings JSON for client-side screen switching
    _stn_data = {}
    _ns = 2 if if_long == 128 else 3
    for _i in range(1, _ns + 1):
        _si = str(_i)
        _st = s["stations"][_si]
        _stn_data[_si] = {"op": _st["operator"], "co": _st["country"],
            "ms": _st["mystation"],
            "M": int(_st["METRO"]), "B": int(_st["BUS"]),
            "T": int(_st["TRAIN"]), "R": int(_st["TRAM"]),
            "S": int(_st["SHIP"]),
            "r": int(_st["red"]), "g": int(_st["green"]), "b": int(_st["blue"]),
            "bo": int(_st["buses_option"]),
            "of": int(_st["offset"]), "di": int(_st["direction"])}
    stn_json = json.dumps(_stn_data)

    # screen buttons
    screen_btns = ""
    screen_btn_disp = ""
    if if_long > 64:
        if not int(s["multiple"]):
            screen_btn_disp = "display:none;"
        ns = 2 if if_long == 128 else 3
        _p = []
        for i in range(1, ns + 1):
            _si = str(i)
            _cls = "scr-btn act" if _si == str(num) else "scr-btn"
            _p.append("<button class='" + _cls + "' type='button' onclick=\"pickScr(" + _si + ")\">"+_si+"</button>")
        screen_btns = "".join(_p)

    # search disable
    search_dis = "" if connected else "disabled"
    station_ph = T["not_connected"] if not connected else stn["mystation"]

    # results
    result_dis = "disabled"
    result_style = ""
    if varinit.results:
        result_dis = ""
        result_style = "style='background:#2a1215;border-color:#dc3545;animation:guide-pulse 2.5s ease-in-out infinite'"

    # maxdest options
    _p = []
    for i in range(1, 21):
        _p.append(_opt(i, s["maxdest"], str(i)))
    maxdest_opt = "".join(_p)


    # metro section
    metro_html = ""
    hasMetro = op in ("SL", "HSL", "BE", "KB", "NO")
    #if hasMetro:
    metro_html = _chk("METRO", stn["METRO"], "/?type=metro", T["subway"])

    # SL line color buttons (always in DOM, visibility toggled by JS)
    rc = " checked" if int(stn["red"]) else ""
    gc = " checked" if int(stn["green"]) else ""
    bc = " checked" if int(stn["blue"]) else ""
    sl_disp = "" if op == "SL" else "display:none;"
    sl_colors = '<div id="slcolors" style="' + sl_disp + '"><input type="checkbox" class="btn-check" id="r" name="red" data-u="/?line=red"' + rc + '><label class="btn btn-danger" for="r"> </label> <input type="checkbox" class="btn-check" id="g" name="green" data-u="/?line=green"' + gc + '><label class="btn btn-success" for="g"> </label> <input type="checkbox" class="btn-check" id="b" name="blue" data-u="/?line=blue"' + bc + '><label class="btn btn-primary" for="b"> </label></div>'

    # bus section
    bus_html = ""
    if op != "SJ":
        bus_html = _chk("BUS", stn["BUS"], "/?type=bus", T["buses"])

    # SL bus options (always in DOM, visibility toggled by JS)
    bopt_all = "" if int(stn["buses_option"]) else " checked"
    bopt_night = " checked" if int(stn["buses_option"]) else ""
    sl_bus_disp = "" if op == "SL" else "display:none;"
    sl_bus_opts = ''.join(['<div id="slbusopts" style="', sl_bus_disp, '"><details><summary>&#x279C; <small>', T["more"], '</small></summary><small>',
        '<div class="form-check"><input class="form-check-input" type="radio" name="buses_option" id="all_buses" value="option1" data-u="/?buses_option=0" data-e="click"', bopt_all, '><label class="form-check-label" for="all_buses">', T["all_buses"], '</label></div>',
        '<div class="form-check"><input class="form-check-input" type="radio" name="buses_option" id="night_buses" value="option2" data-u="/?buses_option=1" data-e="click"', bopt_night, '><label class="form-check-label" for="night_buses">', T["only_nightbuses"], '</label></div></small></details></div>'])

    # train
    train_html = _chk("TRAIN", stn["TRAIN"], "/?type=train", T["trains"])

    # tram
    tram_html = ""
    if op != "SJ":
        tram_html = _chk("TRAM", stn["TRAM"], "/?type=tram", T["trams"])

    # ship
    ship_html = ""
    if op != "SJ":
        ship_html = _chk("SHIP", stn["SHIP"], "/?type=ship", T["ships"])

    # SL line color buttons (always in DOM, visibility toggled by JS)
    rc = " checked" if int(stn["red"]) else ""
    gc = " checked" if int(stn["green"]) else ""
    bc = " checked" if int(stn["blue"]) else ""
    sl_disp = "" if op == "SL" else "display:none;"
    sl_colors = '<div id="slcolors" style="' + sl_disp + '"><input type="checkbox" class="btn-check" id="r" name="red" data-u="/?line=red"' + rc + '><label class="btn btn-danger" for="r"> </label> <input type="checkbox" class="btn-check" id="g" name="green" data-u="/?line=green"' + gc + '><label class="btn btn-success" for="g"> </label> <input type="checkbox" class="btn-check" id="b" name="blue" data-u="/?line=blue"' + bc + '><label class="btn btn-primary" for="b"> </label></div>'

    # SL bus options (always in DOM, visibility toggled by JS)
    bopt_all = "" if int(stn["buses_option"]) else " checked"
    bopt_night = " checked" if int(stn["buses_option"]) else ""
    sl_bus_disp = "" if op == "SL" else "display:none;"
    sl_bus_opts = ''.join(['<div id="slbusopts" style="', sl_bus_disp, '"><details><summary>&#x279C; <small>', T["more"], '</small></summary><small>',
        '<div class="form-check"><input class="form-check-input" type="radio" name="buses_option" id="all_buses2" value="option1" data-u="/?buses_option=0" data-e="click"', bopt_all, '><label class="form-check-label" for="all_buses2">', T["all_buses"], '</label></div>',
        '<div class="form-check"><input class="form-check-input" type="radio" name="buses_option" id="night_buses2" value="option2" data-u="/?buses_option=1" data-e="click"', bopt_night, '><label class="form-check-label" for="night_buses2">', T["only_nightbuses"], '</label></div></small></details></div>'])

    # offset options
    _p = []
    for i in range(0, 31):
        _p.append(_opt(i, stn["offset"], str(i) + " min"))
    offset_opt = "".join(_p)

    # direction (SL only)
    dir_html = ""
    #if op == "SL":
    dirs = [D["north_south"], D["north"], D["south"]]
    _p = ['<label class="control-label" for="direction">', T["direction"], ':</label><select id="direction" name="direction" class="form-control" data-p="direction" data-e="change">']
    for i in range(3):
        _p.append(_opt(i, stn["direction"], dirs[i]))
    _p.append("</select>")
    dir_html = "".join(_p)

    # brightness options
    bright_opt = ""
    if if_long > 64:
        bright_opt = "<option value='0' selected>Normal</option>"
    else:
        brl = [T["low"], T["middle"], T["high"]]
        _p = []
        for i in range(3):
            _p.append(_opt(i, s["brightness"], brl[i]))
        bright_opt = "".join(_p)

    # scroll section (128 only)
    scroll_html = ""
    if if_long == 128:
        scroll_html = ''.join(['<div class="col"><label for="scroll">', T["scroll"], ':</label><select id="scroll" name="scroll" class="form-control" data-p="scroll" data-e="change">', _opt(0, s["scroll"], "Normal"), _opt(1, s["scroll"], T["low"]), '</select></div>'])

    # list mode
    listmode_html = ""
    if if_long > 64 and varinit.display.height <= 32:
        listmode_html = _chk("abc", s["listmode"], "/?listmode=switch", T["list"])

    # clocktime
    clock_html = _chk("clocktime", s["clocktime"], "/?clocktime=switch", T["clocktime"])

    # multiple (>64 only)
    mult_html = ""
    if if_long > 64:
        mult_html = _chk("multiple", s["multiple"], "/?multiple=1", T["multiple"])

    # deviations (SL only)
    devs_html = ""
    if op == "SL":
        devs_html = _chk("show_msgs", s["show_msgs"], "/?show_msgs=1", T["t_info"])

    # sleep
    sleep_html = _chk("sleep", s["sleep"], "/?sleep=1", T["turn_off"])

    # button mode
    button_mode_html = ""
    if if_long > 64 and varinit.display.height <= 32:
        button_mode_html = _chk("button_mode", s.get("button_mode", 0), "/?button_mode=switch", T["button_mode"])

    # show station
    show_stn_html = _chk("show_my_station", s["show_my_station"], "/?show_station=1", T["show_station"])

    # white button (128 only)
    white_btn = ""
    if if_long == 128:
        white_btn = '<button style="background:#fff;border:1px solid #666;color:#111;padding:2px 8px;border-radius:6px;cursor:pointer" type="button" data-u="/?color=2">' + T["white"] + '</button>'

    # listcolor
    listcolor_html = _chk("LISTCOLOR", s["listcolor"], "/?listcolor=switch", T["list_colors_line"])
    listcolor_time_html = _chk("LISTCOLOR_TIME", s.get("listcolor_time", 0), "/?listcolor_time=switch", T["list_colors_time"])

    # font size segmented control (mini / small / large)
    _fs = "mini" if s["mini"] else ("large" if s.get("large_list", 0) else "small")
    _act = "background:#e09d00;color:#111"
    _inact = "background:transparent;color:#aaa"
    _bs = 'border:none;cursor:pointer;font-size:.85rem;padding:3px 10px;'
    font_size_html = (
        '<span style="display:inline-flex;border:1px solid #555;border-radius:5px;overflow:hidden">'
        '<button type="button" onclick="setFont(\'mini\',this)" style="' + _bs + (_act if _fs == "mini" else _inact) + '">mini</button>'
        '<button type="button" onclick="setFont(\'small\',this)" style="' + _bs + 'border-left:1px solid #555;border-right:1px solid #555;' + (_act if _fs == "small" else _inact) + '">small</button>'
        '<button type="button" onclick="setFont(\'large\',this)" style="' + _bs + (_act if _fs == "large" else _inact) + '">large</button>'
        '</span>'
    )
    font_size_row = '<tr><td><b>' + T["font_mini"] + '</b></td><td>' + font_size_html + '</td></tr>' if if_long > 64 else ""
    xs_line_id_row = '<tr><td><b>XS line ID</b></td><td>' + _chk("XS_LINE_ID", s.get("xs_line_id", 0), "/?xs_line_id=switch", "SHOW LINE ID") + '</td></tr>' if if_long <= 64 else ""
    # dest_scroll
    dest_scroll_html = _chk("DEST_SCROLL", s.get("dest_scroll", 0), "/?dest_scroll=switch", "Scroll long names (experimental)")

    # rt_indicator
    rt_indicator_html = _chk("RT_INDICATOR", s["rt_indicator"], "/?rt_indicator=switch", T["rt_indicator"])

    # dns section
    dns_html = ""
    if varinit.dns:
        dns_html = ''.join([
            '<details><summary>&#x279C; &#127760; <small>DNS</small></summary></form>',
            '<form action="/setdns" method="POST"><table>',
            '<tr><td><label>IP:</label></td><td><input type="text" id="ip" name="ip" required></td></tr>',
            '<tr><td><label>Netmask:</label></td><td><input type="text" id="netmask" name="netmask" required></td></tr>',
            '<tr><td><label>Gateway:</label></td><td><input type="text" id="gateway" name="gateway" required></td></tr>',
            '<tr><td><label>DNS (', T["not_required"], '):</label></td><td><input type="text" id="dns_input" name="dns"></td></tr>',
            '<tr><td></td><td><input type="submit" value="', T["save"], '"> ',
            "<button style='background-color:pink;border:1px solid black;color:black;padding:2px;text-align:center;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer' type='button' onclick=\"location.href='/setdns?clear=true'\">", T["clear"], '</button></td></tr>',
            '</table></form></details>'])

    # instructions text
    instr = T["_instructions"] if connected else T["instructions"]

    # build page using pre-split template (single pass, no scanning)
    _v = {
        "CSS": css, "TITLE": T["title"],
        "HEADER": T["title"] + "",
        "CONN_STATUS": conn,
        "ONOFF_CHK": "checked" if int(varinit.on_off_counter) else "",
        "VERSION_TEXT": vmsg, "UPDATE_DIS": update_dis,
        "T_INFO": T["info"], "IP_DISPLAY": ip, "INSTR_TEXT": instr,
        "T_NETWORK": T["network"], "SSID_OPTIONS": ssid_opt,
        "NET_DIS": net_dis, "T_PASSWORD": T["password"],
        "T_CONNECT": T["connect"], "COUNTRY_FLAG": country_flag,
        "OPERATOR": op, "COMBINED_LIST": combined_list,
        "SCREEN_BUTTONS": screen_btns, "SCREEN_BTN_DISP": screen_btn_disp,
        "STATION_PH": station_ph, "SEARCH_DIS": search_dis,
        "T_SEARCH": T["_search"],
        "OPBTN_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (not co or not stn["operator"]) else "",
        "SSTRING_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (co and stn["operator"] and connected and not stn["mystation"]) else "",
        "RESULTS": varinit.results, "RESULT_DIS": result_dis,
        "RESULT_STYLE": result_style,
        "T_NO_DEPARTURES": T["no_departures"],
        "MAXDEST_OPTIONS": maxdest_opt,
        "METRO_SECTION": metro_html, "SL_COLORS": sl_colors,
        "BUS_SECTION": bus_html, "SL_BUS_OPTIONS": sl_bus_opts,
        "TRAIN_CHK": train_html, "TRAM_SECTION": tram_html,
        "SHIP_SECTION": ship_html,
        "T_HIDE_DEPARTURES": T["hide_departures"],
        "OFFSET_OPTIONS": offset_opt,
        "DIRECTION_SECTION": dir_html,
        "T_BRIGHTNESS": T["brightness"],
        "BRIGHTNESS_OPTIONS": bright_opt,
        "SCROLL_SECTION": scroll_html,
        "SCROLL_LABEL": T["scroll"],
        "DIRECTION_LABEL": T["direction"],
        "T_TRAFFIC_TYPES": T["traffic_types"],
        "LISTMODE_CHK": listmode_html, "CLOCKTIME_CHK": clock_html,
        "MULTIPLE_SECTION": mult_html,
        "DEVIATIONS_SECTION": devs_html,
        "SLEEP_CHK": sleep_html, "BUTTON_MODE_CHK": button_mode_html, "SHOW_STATION_CHK": show_stn_html,
        "T_SAVE": T["save"], "T_USER": T["user"],
        "USER_PH": str(s["user"]),
        "T_ADVANCED": T["advanced"],
        "T_ADVANCED_SETTINGS": T["advanced_settings"],
        "T_TEMP": T["temp"],
        "TEMP_VAL": str(round(microcontroller.cpu.temperature)),
        "UPTIME_VAL": str(uptime), "T_MINUTES": T["minutes"],
        "T_ANGLE": T["angle"], "T_ROTATION": T["rotation"],
        "T_WIDTH": T["width"],
        "T_SYSTEM_LANGUAGE": T["system_language"], "LANG": lg,
        "T_TONE": T["tone"], "T_ORANGE": T["orange"],
        "T_YELLOW": T["yellow"], "WHITE_BTN": white_btn,
        "T_LIST_COLORS": T["list_colors"],
        "LISTCOLOR_CHK": listcolor_html,
        "LISTCOLOR_TIME_CHK": listcolor_time_html,
        "FONT_SIZE_ROW": font_size_row,
        "XS_LINE_ID_ROW": xs_line_id_row,
        "DEST_SCROLL_CHK": dest_scroll_html,
        "DNS_SECTION": dns_html,
        "T_ROTATION": T.get("rotation", "Rotation"),
        "RT_INDICATOR_CHK": rt_indicator_html,
        "T_RT_INDICATOR": T["rt_indicator"],
        "T_POWER": T["power"],
        "POWER_VAL": str(s["power"]),
        "T_LINE_LENGTH": T["line_length"],
        "LINE_LENGTH_VAL": str(s["line_length"]),
        "T_SHOW_LINES": T["show_lines"],
        "SHOW_LINES_VAL": ",".join(s["show_lines"]) if isinstance(s["show_lines"], list) else str(s["show_lines"]),
        "STRIP_DEST_VAL": ",".join(s.get("strip_dest", [])) if isinstance(s.get("strip_dest"), list) else str(s.get("strip_dest", "")),
        "T_NO_MORE_DEP": T["no_more_departures_label"],
        "NO_MORE_DEP_VAL": str(s["no_more_departures"]),
        "T_MINS": T["mins_label"],
        "MINS_VAL": str(s["mins"]),
        "CONN_OK": conn_ok, "CONN_FAIL": conn_fail,
        "OPS_JSON": ops_json, "STN_JSON": stn_json,
    }
    _out = []
    for _frag, _key in _PARTS:
        _out.append(_frag)
        if _key: _out.append(_v.get(_key, ""))
    return "".join(_out)


def timer(_language, timer):
  for i in timer:
    try: timer[i][1]
    except: timer[i] = ["00:00","00:00"]

  return """<!DOCTYPE html><html>
<meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">
<title>Timer</title>
<style>""" + css + """</style>
<body><div class="container"><div class="header">
<div class="form-group">
<hr>
<div class="p-1 mb-0 bg-warning text-dark font-weight-bold">""" + language[_language]["settings"]["timer_title"] + """</div>
<hr>

<form action="?set_timer=true" method="GET">

<b>""" + language[_language]["settings"]["monday"] + """</b>
<div><input type="time" id="mondayS" value=""" + timer["Monday"][0] + """> - <input type="time" id="mondayE" value=""" + timer["Monday"][1] + """></div>
<script>
var ms=document.getElementById("mondayS"),me=document.getElementById("mondayE");
function mSend(){if(ms.value&&me.value)fetch('/?set_timer=Monday&start='+encodeURIComponent(ms.value+'to='+me.value),{method:'GET'})}
ms.addEventListener("change",mSend);me.addEventListener("change",mSend);
</script>

<b>""" + language[_language]["settings"]["tuesday"] + """</b>
<div><input type="time" id="tuesdayS" value=""" + timer["Tuesday"][0] + """> - <input type="time" id="tuesdayE" value=""" + timer["Tuesday"][1] + """></div>
<script>
var tus=document.getElementById("tuesdayS"),tue=document.getElementById("tuesdayE");
function tuSend(){if(tus.value&&tue.value)fetch('/?set_timer=Tuesday&start='+encodeURIComponent(tus.value+'to='+tue.value),{method:'GET'})}
tus.addEventListener("change",tuSend);tue.addEventListener("change",tuSend);
</script>

<b>""" + language[_language]["settings"]["wednesday"] + """</b>
<div><input type="time" id="wednesdayS" value=""" + timer["Wednesday"][0] + """> - <input type="time" id="wednesdayE" value=""" + timer["Wednesday"][1] + """></div>
<script>
var ws=document.getElementById("wednesdayS"),we=document.getElementById("wednesdayE");
function wSend(){if(ws.value&&we.value)fetch('/?set_timer=Wednesday&start='+encodeURIComponent(ws.value+'to='+we.value),{method:'GET'})}
ws.addEventListener("change",wSend);we.addEventListener("change",wSend);
</script>

<b>""" + language[_language]["settings"]["thursday"] + """</b>
<div><input type="time" id="thursdayS" value=""" + timer["Thursday"][0] + """> - <input type="time" id="thursdayE" value=""" + timer["Thursday"][1] + """></div>
<script>
var ths=document.getElementById("thursdayS"),the_=document.getElementById("thursdayE");
function thSend(){if(ths.value&&the_.value)fetch('/?set_timer=Thursday&start='+encodeURIComponent(ths.value+'to='+the_.value),{method:'GET'})}
ths.addEventListener("change",thSend);the_.addEventListener("change",thSend);
</script>

<b>""" + language[_language]["settings"]["friday"] + """</b>
<div><input type="time" id="fridayS" value=""" + timer["Friday"][0] + """> - <input type="time" id="fridayE" value=""" + timer["Friday"][1] + """></div>
<script>
var fs=document.getElementById("fridayS"),fe=document.getElementById("fridayE");
function fSend(){if(fs.value&&fe.value)fetch('/?set_timer=Friday&start='+encodeURIComponent(fs.value+'to='+fe.value),{method:'GET'})}
fs.addEventListener("change",fSend);fe.addEventListener("change",fSend);
</script>

<b>""" + language[_language]["settings"]["saturday"] + """</b>
<div><input type="time" id="saturdayS" value=""" + timer["Saturday"][0] + """> - <input type="time" id="saturdayE" value=""" + timer["Saturday"][1] + """></div>
<script>
var sas=document.getElementById("saturdayS"),sae=document.getElementById("saturdayE");
function saSend(){if(sas.value&&sae.value)fetch('/?set_timer=Saturday&start='+encodeURIComponent(sas.value+'to='+sae.value),{method:'GET'})}
sas.addEventListener("change",saSend);sae.addEventListener("change",saSend);
</script>

<b>""" + language[_language]["settings"]["sunday"] + """</b>
<div><input type="time" id="sundayS" value=""" + timer["Sunday"][0] + """> - <input type="time" id="sundayE" value=""" + timer["Sunday"][1] + """></div>
<script>
var sus=document.getElementById("sundayS"),sue=document.getElementById("sundayE");
function suSend(){if(sus.value&&sue.value)fetch('/?set_timer=Sunday&start='+encodeURIComponent(sus.value+'to='+sue.value),{method:'GET'})}
sus.addEventListener("change",suSend);sue.addEventListener("change",suSend);
</script>

<button type="button" onclick="location.href='/'">""" + language[_language]["settings"]["return"] + """</button>
<button style="background-color:pink;border:1px solid black;color:black;padding:2px;text-align:center;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer" type="button" onclick="location.href='/?cleartimer=true'">""" + language[_language]["settings"]["clear"] + """</button>

</form>
</div></div></body></html>"""
