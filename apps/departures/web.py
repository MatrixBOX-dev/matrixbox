css = ""
try: from css import _css as css
except: pass
from dicts import language, flag as _flag_img

country_and_operators = {
  "se":[["sl","SL (Stockholm)"],["vt","VT (Västtrafik)"],["otraf","Östgötatrafiken"],["vastmanland","VL (Västmanlands län)"],["dt","DT (Dalatrafik)"],["jlt","JLT (Jönköpings län)"],["krono","KRONO (Kronobergs länstrafik)"],["ul","UL (Uppsala län)"],["klt","KLT (Kalmar länstrafik)"],["orebro","Länstrafiken Örebro"],["xt","X-Trafik (Gävleborg)"],["varm","Värmlandstrafik - Karlstadsbuss"],["skane","Skånetrafiken"],["norrbotten","Norrbotten"],["fe","Trafikverkets färjor"],["dintur","DinTur (Västernorrland)"],["sj","SJ (Trafikverket)"],["sormland","Sörmland (Endast tidtabell)"]],
  "dk":[["kb","Scheduled"],["dk_rt","Real-time (experimental)"]],
  "lu":[["all","All of Luxembourg"]],
  "no":[["no","Entur (entire Norway)"]],
  "fi":[["all","All of Finland"], ["hsl","HSL"]],
  "cr":[["za","ZET (Zagreb)"]],
  "nl":[["all","Countrywide"], ["ns","Nederlandse Spoorwegen"]],
  "ch":[["ch","Switzerland"],["sbb","SBB"]],
  "fr":[["sncf","SNCF"], ["idfm","IDFM (Paris)"], ["ilevia","Ilévia"], ["met","Le MET"]],
  "lt":[["vil","Vilnius"]],
  "be":[["sncb","SNCB"], ["stib","STIB"], ["delijn","De Lijn"]],
  "uk":[["lo","Tfl (London)"],["nr","National Rail"]],
  "hu":[["bu","Budapest"]],
  "us":[["nyc_subway","NYC Subway"],["nyc_lirr","Long Island Rail Road"],["nyc_mnr","Metro-North Railroad"],["nyc_bus_bx","MTA Bus - Bronx"],["nyc_bus_b","MTA Bus - Brooklyn"],["nyc_bus_m","MTA Bus - Manhattan"],["nyc_bus_q","MTA Bus - Queens"],["nyc_bus_si","MTA Bus - Staten Island"],["nyc_bus_co","MTA Bus Company"]],
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
    return ('<div class="toggle-row"><label for="' + name + '" class="toggle-label">' + label + '</label>'
            '<label class="switch"><input type="checkbox" id="' + name + '" data-u="' + url + '"' + c + '><span class="slider"></span></label></div>')


def _toggle2(name, val, url, label_left, label_right, caption=""):
    c = " checked" if int(val) else ""
    cap = '<label for="' + name + '" class="toggle-label">' + caption + '</label>' if caption else ""
    return ('<div class="toggle-row">' + cap +
            '<input type="checkbox" id="' + name + '" class="seg-toggle-cb" data-u="' + url + '"' + c + '>'
            '<label for="' + name + '" class="seg-toggle"><div>' + label_left + '</div><div>' + label_right + '</div></label>'
            '</div>')


def _rssi(functions):
    try:
        ai = functions.wifi.radio.ap_info
        return ai.rssi if ai else -100
    except Exception:
        return -100


def _sig_bars(rssi):
    n = 5 if rssi > -45 else 4 if rssi > -55 else 3 if rssi > -65 else 2 if rssi > -75 else 1 if rssi > -85 else 0
    bars = "".join('<i class="' + ("on" if i < n else "") + '"></i>' for i in range(5))
    return '<span class="sig" id="sig" title="' + str(rssi) + ' dBm">' + bars + "</span>"


PAGE_TPL = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">
<link href="data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAA/SURBVDhPY2RgYPgPxGQDsAFAAOGRCBgZGREGgDikAJgeJiifbDDwBuAMRPQwwaVmGITBqAHUykwQLjmAgQEA3oYYFR16cP8AAAAASUVORK5CYII=" rel="icon" type="image/x-icon"/>
<title>{TITLE}</title><style>{CSS}</style></head><body>
<nav class="navbar">
<a class="nav-x" href="/exit" title="Exit" style="margin-left:0;margin-right:4px">&#8592;</a>
<span class="nav-title">{HEADER}</span>
<form method="post" action="/" class="wifi-nav-form">
<details class="wifi-nav">
<summary>&#9881; {T_WIFI_LABEL}</summary>
<div class="wifi-nav-panel">
<div class="form-row">
<div class="col">
<label for="ssid"><a href="#" onclick="doScan();return false" title="Scan">&#128268;</a> {T_WIFI_LABEL}</label>
<select id="ssid" class="form-control" name="ssid" data-p="ssid" data-e="change" {NET_DIS}>{SSID_OPTIONS}</select>
</div>
<div class="col">
<label for="password">{T_PASSWORD}</label>
<input type="text" id="password" class="form-control" name="password" placeholder="*******" data-p="password" data-e="blur" data-enc="1" {NET_DIS}>
</div>
</div>
<button type="button" class="btn btn-outline-secondary btn-sm" id="connect_wifi" style="margin-top:8px" data-u="/?connect_wifi=true" {NET_DIS}>{T_CONNECT}</button>
</div>
</details>
</form>
<div class="nav-info"><span id="clk"></span><span>{IP_DISPLAY}</span></div>
{SIG_BARS}
<button type="button" class="nav-led{LED_OFF_CLS}" id="ledbtn" onclick="fetch('/?onoff=active').then(function(){document.getElementById('ledbtn').classList.toggle('led-off')})" title="Turn display on/off">&#x1F4A1;</button>
<a class="nav-x" href="/exit" title="Exit">&#x2715;</a>
</nav>
<div class="page">
<header class="brand-header">
<button type="button" class="brand-lockup" id="brand-lockup" aria-label="Edit email address" aria-controls="signup-card" aria-expanded="true">
<span class="brand-mark" aria-hidden="true"><span>T</span><small>SKYLT</small></span>
<span class="brand-name">Departures</span>
</button>
<a class="signup-link" href="http://subscription.t-skylt.se/" target="_blank" rel="noopener noreferrer">Sign up!</a>
</header>
<div class="card signup-card" id="signup-card">
<input type="email" id="signup-email" class="form-control" value="{USER_EMAIL}" placeholder="your.name@example.com" autocomplete="email" aria-label="Email address">
</div>
<form method="post" action="/">
<div class="card">
<div class="section-title">{T_STATION_DISPLAY}</div>
{SKIN_SECTION}
{VBZ_SETTINGS_SECTION}
{UBAHN_SETTINGS_SECTION}
{MULTIPLE_SECTION}
<div class="form-row" style="margin-top:12px">
<div id="operator_picker" style="{OPERATOR_PICKER_DISP}">
<div class="dropdown" id="opdd"><button type="button" class="dropbtn" id="opbtn" {OPBTN_PULSE} onclick="toggleDropdown(event)">{COUNTRY_FLAG} {OPERATOR} &#9660;</button>
<div class="dropdown-content">{COMBINED_LIST}</div></div>
</div>
{DSA_PROVIDER_SECTION}
<div id="screenbtns" style="{SCREEN_BTN_DISP}display:flex;align-items:center;gap:6px">
<span style="font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">Editing</span>
{SCREEN_BUTTONS}
</div>
<div class="col" style="min-width:150px">
<select id="newstation" class="form-control" name="newstation" data-p="newstation" data-e="change" {RESULT_DIS} {RESULT_STYLE} onchange="this.style.animation=''">{RESULTS}</select>
</div>
</div>
<div class="form-row" style="margin-top:10px">
<div class="col">
<input type="text" id="sstring" class="form-control" name="sstring" placeholder="{STATION_PH}" {SEARCH_DIS} {SSTRING_PULSE} onkeydown="if(event.key==='Enter'){event.preventDefault();doSearch()}">
</div>
<button type="button" class="btn" id="searchbtn" onclick="doSearch()" {SEARCH_DIS}>{T_SEARCH}</button>
</div>
</div>
<div class="card">
<div class="grp-title">{T_TRAFFIC_TYPES}</div>
<div class="tt-grid">
{METRO_SECTION}
{BUS_SECTION}
{TRAIN_CHK}
{TRAM_SECTION}
{SHIP_SECTION}
</div>
{SL_SECTION}
</div>
<div class="card">
{CLOCKTIME_CHK}
{DEVIATIONS_SECTION}
{DISRUPTIONS}

{BUTTON_MODE_CHK}
{SLEEP_CHK}
{SHOW_STATION_CHK}
</div>
<div class="card">
<div class="grp">
<div class="form-row">{SCROLL_SECTION}<div class="col">
<label for="maxdest">{T_NO_DEPARTURES}</label>
<select id="maxdest" name="maxdest" class="form-control" data-p="maxdest" data-e="change">{MAXDEST_OPTIONS}</select>
</div></div></div>
<div class="grp">
<div class="form-row"><div class="col">
<label for="offset">{T_HIDE_DEPARTURES}</label>
<select id="offset" name="offset" class="form-control" data-p="offset" data-e="change">{OFFSET_OPTIONS}</select>
</div><div class="col">{DIRECTION_SECTION}</div></div></div>
</div>
<div class="card"><details>
<summary>&#9881; {T_ADVANCED}</summary>
<table>
<tr><td><b>{T_TONE}</b></td><td><div style="display:flex;gap:10px">{TONE_SWATCHES}</div></td></tr>
{FONT_SIZE_ROW}
{CLOCK_ROW_HTML}
{DLR_SETTINGS_SECTION}
<tr><td><b>Timer</b></td><td><button type="button" class="btn btn-sm" onclick="location.href='/?timer=set'">&#8987; Configure</button></td></tr>
<tr><td><b>{T_ROTATION}</b></td><td><button type="button" class="btn btn-sm" data-u="/?rotate=1">&#128260; 90&deg;</button></td></tr>
<tr><td><b>{T_POWER}</b></td><td><input type="text" id="power" class="form-control" style="width:80px;display:inline" placeholder="{POWER_VAL}" data-p="power" data-e="blur"></td></tr>
<tr><td><b>{T_LINE_LENGTH}</b></td><td><input type="text" id="line_length" class="form-control" style="width:80px;display:inline" placeholder="{LINE_LENGTH_VAL}" data-p="line_length" data-e="blur"><br><small>{T_LINE_LENGTH_HELP}</small></td></tr>
<tr><td><b>{T_SHOW_LINES}</b></td><td><input type="text" id="show_lines" class="form-control" style="width:160px;display:inline" placeholder="{SHOW_LINES_VAL}" data-p="show_lines" data-e="blur"></td></tr>
<tr><td><b>Strip from destination</b></td><td><input type="text" id="strip_dest" class="form-control" style="width:160px;display:inline" placeholder="{STRIP_DEST_VAL}" data-p="strip_dest" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>Destination abbreviations</b></td><td><input type="text" id="dest_abbrev" class="form-control" style="width:160px;display:inline" placeholder="{DEST_ABBREV_VAL}" data-p="dest_abbrev" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>{T_NO_MORE_DEP}</b></td><td><input type="text" id="no_more_departures" class="form-control" style="width:160px;display:inline" placeholder="{NO_MORE_DEP_VAL}" data-p="no_more_departures" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>{T_MINS}</b></td><td><input type="text" id="mins" class="form-control" style="width:160px;display:inline" placeholder="{MINS_VAL}" data-p="mins" data-e="blur" data-enc="1"></td></tr>
{SKIN_DELETE_SECTION}
</table>
{RT_INDICATOR_CHK}
{XS_LINE_ID_CHK}
{MULTI_STATION_LINE_ID_CHK}
{LISTCOLOR_CHK}
{LISTCOLOR_TIME_CHK}
{DEST_SCROLL_CHK}
{DNS_SECTION}
</details></div>
<button type="button" class="btn btn-full" data-u="/?save=true">&#128190; {T_SAVE}</button>
<div style="text-align:center;margin-top:14px"><small>For support, visit <a href="http://t-skylt.se">T-Skylt.se</a></small></div>
<div id="opsdata" style="display:none">{OPS_JSON}</div>
<div id="stndata" style="display:none">{STN_JSON}</div>
<script>
function _ck(){var d=new Date(),h=d.getHours(),m=d.getMinutes();document.getElementById('clk').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}_ck();setInterval(_ck,15000);
var OPS=JSON.parse(document.getElementById('opsdata').textContent);var STN=JSON.parse(document.getElementById('stndata').textContent);
function toggleDropdown(e){e.stopPropagation();document.getElementById('opdd').classList.toggle('open');}
document.addEventListener('click',function(e){var dd=document.getElementById('opdd');if(dd&&!dd.contains(e.target))dd.classList.remove('open');});
function pickScr(n){fetch('/?screen='+n);var d=STN[n];if(!d)return;document.querySelectorAll('.scr-btn').forEach(function(b){b.classList.toggle('act',b.textContent==String(n));});var co=d.co,op=d.op.toLowerCase();var el=document.querySelector('.dd-grid img[data-c="'+co+'"]');var f=el?el.outerHTML.replace(/dd-sel/g,'')+' ':'';var nm=d.op?d.op.toUpperCase():'OPERATOR';var ops=OPS[co]||[];for(var i=0;i<ops.length;i++){if(ops[i][0]===op){nm=ops[i][1];break;}}document.getElementById('opbtn').innerHTML=f+nm+' &#9660;';document.getElementById('sstring').placeholder=d.ms||'';var cb={METRO:d.M,BUS:d.B,TRAIN:d.T,TRAM:d.R,SHIP:d.S,r:d.r,g:d.g,b:d.b};for(var k in cb){var e=document.getElementById(k);if(e)e.checked=!!cb[k];}var sl=document.getElementById('slsection');if(sl)sl.style.display=op==='sl'?'':'none';var nb=document.getElementById('night_buses');if(nb)nb.checked=!!d.bo;var of2=document.getElementById('offset');if(of2)of2.value=d.of;var di=document.getElementById('direction');if(di)di.value=d.di;}
function pickC(c){var d=document.getElementById('ddops');d.innerHTML='';var ops=OPS[c]||[];for(var i=0;i<ops.length;i++){var a=document.createElement('a');a.href='#';a.textContent=ops[i][1];(function(cc,code,name){a.onclick=function(e){e.preventDefault();chCO(cc,code,name);return false;};})(c,ops[i][0],ops[i][1]);d.appendChild(a);}document.querySelectorAll('.dd-grid img').forEach(function(im){im.classList.toggle('dd-sel',im.dataset.c===c);});}
function chCO(c,o,n){fetch('/?country='+c+'&operator='+o);var el=document.querySelector('.dd-grid img[data-c="'+c+'"');var f='';if(el)f=el.outerHTML.replace(/dd-sel/g,'')+' ';document.getElementById('opbtn').innerHTML=f+n+' &#9660;';document.getElementById('opbtn').style.animation='';document.getElementById('sstring').style.animation='guide-pulse 2.5s ease-in-out infinite';var sl=document.getElementById('slsection');if(sl)sl.style.display=o==='sl'?'':'none';document.getElementById('opdd').classList.remove('open');}
function doSearch(){var s=document.getElementById('sstring').value;if(!s)return;var b=document.getElementById('searchbtn');b.disabled=true;b.innerHTML='<span class="spin"></span>';fetch('/search?sstring='+encodeURIComponent(s)).then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('newstation');sel.innerHTML=h;sel.disabled=false;sel.style.borderColor='#ff6060';sel.style.animation='guide-pulse 2.5s ease-in-out infinite';document.getElementById('sstring').style.animation='';b.disabled=false;b.textContent='{T_SEARCH}';}).catch(function(){b.disabled=false;b.textContent='{T_SEARCH}';});}
function doScan(){fetch('/checknet').then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('ssid');sel.innerHTML=h;sel.disabled=false;document.getElementById('password').disabled=false;document.getElementById('connect_wifi').disabled=false;}).catch(function(){});}

var signupEmail=document.getElementById('signup-email');
var brandLockup=document.getElementById('brand-lockup');
function setSignupCollapsed(collapsed){document.body.classList.toggle('email-collapsed',collapsed);brandLockup.setAttribute('aria-expanded',collapsed?'false':'true');}
function isValidSignupEmail(){return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(signupEmail.value.trim());}
var signupSaveTimer;
signupEmail.addEventListener('input',function(){clearTimeout(signupSaveTimer);signupSaveTimer=setTimeout(function(){fetch('/?user='+encodeURIComponent(signupEmail.value.trim())).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);}).catch(function(err){console.error('Could not update email address',err);});},350);});
signupEmail.addEventListener('blur',function(){setSignupCollapsed(isValidSignupEmail());});
brandLockup.addEventListener('click',function(){if(document.body.classList.contains('email-collapsed')){setSignupCollapsed(false);signupEmail.focus();}});
setSignupCollapsed(isValidSignupEmail());

var currentSkin='{CURRENT_SKIN}';
var mc=document.getElementById('multiple');
function updateMultipleControls(){var isList=currentSkin==='list',enabled=isList&&mc&&mc.checked;var ms=document.getElementById('multiple_section');if(ms)ms.style.display=isList?'':'none';var sb=document.getElementById('screenbtns');if(sb)sb.style.visibility=enabled?'visible':'hidden';var sc=document.getElementById('stationcount');if(sc)sc.style.display=enabled?'':'none';}
if(mc)mc.addEventListener('change',updateMultipleControls);
var sk=document.getElementById('skin_select');if(sk)sk.addEventListener('change',function(){currentSkin=sk.value;updateMultipleControls();var d=document.getElementById('dlr_settings_rows');if(d)d.style.display=sk.value==='tfl_dlr'?'':'none';var vb=document.getElementById('vbz_settings_rows');if(vb)vb.style.display=sk.value==='vbz'?'':'none';var ub=document.getElementById('ubahn_settings_rows');if(ub)ub.style.display=sk.value==='ubahn'?'':'none';var op=document.getElementById('operator_picker');if(op)op.style.display=sk.value==='dsa'?'none':'';var dp=document.getElementById('dsa_provider_picker');if(dp)dp.style.display=sk.value==='dsa'?'':'none';});
function setFont(v,el){fetch('/?font_size='+v);var bs=el.parentNode.querySelectorAll('button');bs.forEach(function(b){b.classList.remove('on');});el.classList.add('on');}
function setColor(v,el){fetch('/?color='+v);el.parentNode.querySelectorAll('.color-swatch-btn').forEach(function(b){b.classList.remove('active');});el.classList.add('active');}
document.querySelectorAll('[data-u],[data-p]').forEach(function(el){
el.addEventListener(el.dataset.e||'click',function(ev){
var u=el.dataset.u;
if(el.id==='night_buses')u='/?buses_option='+(el.checked?'1':'0');
if(!u){var v=ev.target.value.replace(/#/g,'%23');if(el.dataset.enc)v=encodeURIComponent(v);u='/?'+el.dataset.p+'='+v;}
fetch(u,{method:'GET'});
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
    import varinit, functions
    num = varinit.screen_selector
    s = varinit.settings
    stn = s["stations"][num]
    lg = s["language"]
    T = language[lg]["settings"]
    D = language[lg]["display"]
    connected = functions.wifi.radio.connected
    cur_skin = functions.get_skin()
    co = stn["country"].lower()
    op_code = stn["operator"].upper()
    op = op_code
    for _op_code, _op_label in country_and_operators.get(co, []):
        if _op_code == stn["operator"].lower():
            op = _op_label
            break
    if not op: op = T["operator"]
    ip = str(functions.wifi.radio.ipv4_address) if connected else "OFFLINE"
    if_long = varinit.if_long

    # ssid options (populated by a /checknet scan; always includes the current ssid)
    _p = ["<option value='", str(s["ssid"]), "' selected>", str(s["ssid"]), "</option>"]
    if hasattr(varinit, "netlist"):
        for n in varinit.netlist:
            _ns = str(n)
            _p.append("<option value='" + _ns + "'>" + _ns + "</option>")
    ssid_opt = "".join(_p)

    # network fields disabled once connected, unless a scan is in progress
    net_dis = "disabled" if connected and not (hasattr(varinit, "checknet") and varinit.checknet) else ""

    # dns section (hidden unless the on-device /dns route has been hit). Closes
    # the page's main form early and opens its own, isolated one, so this
    # submit only posts ip/netmask/gateway/dns to /setdns, not every other
    # setting on the page too.
    dns_html = ""
    if getattr(varinit, "dns", False):
        dns_html = ''.join([
            '</form>',
            '<div class="section-title" style="margin-top:12px">DNS</div>',
            '<form action="/setdns" method="POST"><table>',
            '<tr><td><label>IP</label></td><td><input type="text" id="ip" class="form-control" name="ip" required></td></tr>',
            '<tr><td><label>Netmask</label></td><td><input type="text" id="netmask" class="form-control" name="netmask" required></td></tr>',
            '<tr><td><label>Gateway</label></td><td><input type="text" id="gateway" class="form-control" name="gateway" required></td></tr>',
            '<tr><td><label>DNS (', T["not_required"], ')</label></td><td><input type="text" id="dns_input" class="form-control" name="dns"></td></tr>',
            '</table>',
            '<div class="action-row" style="margin-top:8px">',
            '<button type="submit" class="btn btn-sm">', T["save"], '</button>',
            '<button type="button" class="btn btn-sm btn-danger" onclick="location.href=\'/setdns?clear=true\'">', T["clear"], '</button>',
            '</div></form>'])

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

    # screen buttons (used both for wide side-by-side lists and XS merged list stop selection)
    screen_btns = ""
    screen_btn_disp = ""
    if cur_skin != "list" or not int(s["multiple"]):
        screen_btn_disp = "visibility:hidden;"
    ns = 2 if if_long == 128 else 3
    _p = []
    for i in range(1, ns + 1):
        _si = str(i)
        _cls = "scr-btn act" if _si == str(num) else "scr-btn"
        _p.append("<button class='" + _cls + "' type='button' title='Edit station " + _si + "' onclick=\"pickScr(" + _si + ")\">"+_si+"</button>")
    screen_btns = "".join(_p)

    # search disable
    search_dis = "" if connected else "disabled"
    station_ph = T["not_connected"] if not connected else stn["mystation"]

    # results
    result_dis = "disabled"
    result_style = ""
    if varinit.results:
        result_dis = ""
        result_style = "style='border-color:#ff6060;animation:guide-pulse 2.5s ease-in-out infinite'"

    # maxdest options
    _p = []
    for i in range(1, 21):
        _p.append(_opt(i, s["maxdest"], str(i)))
    maxdest_opt = "".join(_p)

    # metro section
    metro_html = _chk("METRO", stn["METRO"], "/?type=metro", T["subway"])


        

    # SL line color filter chips + night-bus toggle, grouped in one show/hide block
    rc = " checked" if int(stn["red"]) else ""
    gc = " checked" if int(stn["green"]) else ""
    bc = " checked" if int(stn["blue"]) else ""
    sl_disp = "" if op_code == "SL" else "display:none;"
    night_bus_html = _chk("night_buses", stn["buses_option"], "/?buses_option=1", T["only_nightbuses"])
    devs_html = _chk("show_msgs", s["show_msgs"], "/?show_msgs=1", T["t_info"])
    sl_section = ''.join(['<div id="slsection" style="', sl_disp, ';margin-top:10px">',
        '<label class="control-label" style="margin-bottom:6px">Metro line filter</label>',
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">',
        '<input type="checkbox" class="btn-check" id="r" name="red" data-u="/?line=red"', rc, '>',
        '<label class="line-chip" for="r"><span class="dot" style="background:#dc2626"></span>Red</label>',
        '<input type="checkbox" class="btn-check" id="g" name="green" data-u="/?line=green"', gc, '>',
        '<label class="line-chip" for="g"><span class="dot" style="background:#16a34a"></span>Green</label>',
        '<input type="checkbox" class="btn-check" id="b" name="blue" data-u="/?line=blue"', bc, '>',
        '<label class="line-chip" for="b"><span class="dot" style="background:#2563eb"></span>Blue</label>',
        '</div>', night_bus_html, devs_html, '</div>',])

    
    disruptions = devs_html if op_code in ["VT"] else ""


    # bus section
    bus_html = ""
    if op_code != "SJ":
        bus_html = _chk("BUS", stn["BUS"], "/?type=bus", T["buses"])

    # train
    train_html = _chk("TRAIN", stn["TRAIN"], "/?type=train", T["trains"])

    # tram
    tram_html = ""
    if op_code != "SJ":
        tram_html = _chk("TRAM", stn["TRAM"], "/?type=tram", T["trams"])

    # ship
    ship_html = ""
    if op_code != "SJ":
        ship_html = _chk("SHIP", stn["SHIP"], "/?type=ship", T["ships"])

    # offset options
    _p = []
    for i in range(0, 31):
        _p.append(_opt(i, stn["offset"], str(i) + " min"))
    offset_opt = "".join(_p)

    # direction
    dirs = [D["north_south"], D["north"], D["south"]]
    _p = ['<label class="control-label" for="direction">', T["direction"], '</label><select id="direction" name="direction" class="form-control" data-p="direction" data-e="change">']
    for i in range(3):
        _p.append(_opt(i, stn["direction"], dirs[i]))
    _p.append("</select>")
    dir_html = "".join(_p)

    # scroll section (128 only)
    scroll_html = ""
    if if_long == 128:
        scroll_html = ''.join(['<div class="col"><label for="scroll">', T["scroll"], '</label><select id="scroll" name="scroll" class="form-control" data-p="scroll" data-e="change">', _opt(0, s["scroll"], "Normal"), _opt(1, s["scroll"], T["low"]), '</select></div>'])

    # Multiple stations only applies to the built-in list layout.
    mult_html = _chk("multiple", s["multiple"], "/?multiple=1", T["multiple"])

    # station count (XL only: with 3 panels available, side-by-side lists
    # can show either 2 or 3 stations; other devices always fill every
    # panel they have, so there's nothing to pick). Reuses the existing
    # /?width= endpoint, which already maps "x"/"xl" to settings["long"].
    if if_long > 128:
        _cur_width = "xl" if int(s.get("long", 0)) == 1 else "x"
        mult_html += (
            '<div class="toggle-row" id="stationcount" style="' + ("" if int(s["multiple"]) else "display:none;") + '">'
            '<label for="station_count" class="toggle-label">Columns</label>'
            '<select id="station_count" class="form-control" style="width:130px;display:inline" data-p="width" data-e="change">'
            + _opt("x", _cur_width, "2 stations")
            + _opt("xl", _cur_width, "3 stations")
            + '</select></div>'
        )
    mult_html = '<div class="col" id="multiple_section" style="' + ("" if cur_skin == "list" else "display:none;") + '">' + mult_html + '</div>'

    # skin selector: built-in scroll/list, plus any downloadable skins.
    # A dropdown (rather than segmented buttons) scales to an arbitrary
    # number of plugin skins, and reuses the generic data-p/data-e wiring
    # below so picking one is a plain background fetch, not a page reload.
    skin_html = ""
    if if_long > 64 and varinit.display.height <= 64:
        import skinloader
        skin_opts = [("list", T["list_mode"]), ("scroll", T["scroll_mode"])]
        for _sid, _sinfo in skinloader.PLUGIN_SKINS.items():
            skin_opts.append((_sid, _sinfo["label"]))
        skin_select_opts = "".join(_opt(_sid, cur_skin, _label) for _sid, _label in skin_opts)
        skin_html = ('<div class="toggle-row"><label for="skin_select" class="toggle-label">' + T["mode_label"] + '</label>'
                     '<select id="skin_select" class="form-control" style="width:160px;display:inline" data-p="skin" data-e="change">'
                     + skin_select_opts + '</select></div>')

    # TfL DLR skin's own settings. Always rendered (in their own <tbody>) so
    # switching skins only needs a client-side visibility toggle, not a
    # server re-render + page reload.
    _dlr_active = functions.get_skin() == "tfl_dlr"
    dlr_settings_html = (
        '<tbody id="dlr_settings_rows" style="' + ("" if _dlr_active else "display:none;") + '">'
        '<tr><td><b>DLR message dwell</b></td><td><input type="text" id="dlr_scroll_delay" class="form-control" style="width:80px;display:inline" placeholder="' + str(s.get("dlr_scroll_delay", 15)) + '" data-p="dlr_scroll_delay" data-e="blur">'
        '<br><small>Seconds each departure row shows before disruption/custom messages scroll through.</small></td></tr>'
        '<tr><td><b>Custom message</b></td><td>' + _chk("custom_scroll_show", s.get("custom_scroll_show", 0), "/?custom_scroll_show=switch", "Show custom scrolling message") + '</td></tr>'
        '<tr><td><b>Custom message text</b></td><td><input type="text" id="custom_scroll_text" class="form-control" style="width:160px;display:inline" placeholder="' + str(s.get("custom_scroll_text", "")) + '" data-p="custom_scroll_text" data-e="blur" data-enc="1"></td></tr>'
        '</tbody>'
    )

    # VBZ skin's own settings (color toggle). Shown right under the Mode
    # selector in the Station & display card (not Advanced) since it only
    # ever applies while that one skin is active - same show/hide-by-id
    # pattern as DLR/DSA's own skin-exclusive settings use elsewhere.
    _vbz_active = functions.get_skin() == "vbz"
    # Segmented toggle like clocktime's Countdown/Clock time: unchecked (0)
    # highlights the left label, checked (1) highlights the right one - so
    # "Classic" (val 0, no badges) goes left and "Color" (val 1, the
    # existing real-per-line-colors mode) goes right.
    vbz_settings_html = (
        '<div id="vbz_settings_rows" style="' + ("" if _vbz_active else "display:none;") + '">'
        + _toggle2("vbz_color", s.get("vbz_color", 1), "/?vbz_color=switch", "Classic", "Color", "Line colors:")
        + '</div>'
    )

    # U-Bahn Berlin skin's own settings (countdown style toggle) - same
    # show/hide-by-id pattern as VBZ's own skin-exclusive setting above.
    _ubahn_active = functions.get_skin() == "ubahn"
    ubahn_settings_html = (
        '<div id="ubahn_settings_rows" style="' + ("" if _ubahn_active else "display:none;") + '">'
        + _toggle2("ubahn_countdown_style", s.get("ubahn_countdown_style", 0), "/?ubahn_countdown_style=switch",
                   "5'", "in 5 min", "Countdown style:")
        + '</div>'
    )

    # DSA skin's own settings (API provider), shown in place of the ordinary
    # flag/operator picker above - DSA doesn't use data.t-skylt.se stations/
    # operators at all, so that picker is meaningless while it's active.
    _dsa_active = functions.get_skin() == "dsa"
    operator_picker_disp = "display:none;" if _dsa_active else ""
    _dsa_provider_opts = (
        _opt(1, s.get("dsa_api_provider", 1), "Bahn.de: ICE/IC/Regional/SBahn")
        + _opt(2, s.get("dsa_api_provider", 1), "Bahn.de: all services")
        + _opt(3, s.get("dsa_api_provider", 1), "VVO Dresden (EFA)")
    )
    _dsa_layout_opts = (
        _opt(1, s.get("dsa_layout", 1), "Layout 1")
        + _opt(2, s.get("dsa_layout", 1), "Layout 2")
    )
    dsa_provider_html = (
        # flex-basis:100% (not class="col") so this wraps onto its own full-width
        # line in the parent .form-row, instead of squeezing in as one flex:1
        # item alongside operator_picker/screenbtns/newstation and THEN trying
        # to fit two more .col dropdowns inside that already-narrow slice.
        '<div id="dsa_provider_picker" style="flex:1 1 100%;' + ("" if _dsa_active else "display:none;") + '">'
        '<div class="form-row">'
        '<div class="col"><label for="dsa_api_provider" class="control-label">API provider</label>'
        '<select id="dsa_api_provider" class="form-control" data-p="dsa_api_provider" data-e="change">'
        + _dsa_provider_opts + '</select></div>'
        '<div class="col"><label for="dsa_layout" class="control-label">Layout</label>'
        '<select id="dsa_layout" class="form-control" data-p="dsa_layout" data-e="change">'
        + _dsa_layout_opts + '</select></div>'
        '</div>'
        + _chk("dsa_summer_time", s.get("dsa_summer_time", 0), "/?dsa_summer_time=switch",
               "Summer time (DST, +1h)")
        + '</div>'
    )

    # downloaded skin files (Advanced): a delete button for whichever plugin
    # skins currently have local files, so a stuck/broken skin can always be
    # force-reinstalled by deleting + reselecting it - simpler than a
    # separate "check for update" button now that set_skin() already checks
    # automatically each time a skin is (re)activated.
    import skinloader
    _skin_rows = ""
    for _sid, _sinfo in skinloader.PLUGIN_SKINS.items():
        if skinloader.is_downloaded(_sid):
            _skin_rows += (
                '<tr><td><b>' + _sinfo["label"] + '</b></td><td>'
                '<button type="button" class="btn btn-sm btn-danger" '
                'onclick="if(confirm(\'Delete downloaded files for ' + _sinfo["label"]
                + '? It will re-download next time it is selected.\'))fetch(\'/?skin_delete=' + _sid
                + '\').then(function(){location.reload()})">'
                'Delete</button></td></tr>'
            )
    skin_delete_html = ('<tr><td colspan="2"><b>Downloaded skins</b></td></tr>' + _skin_rows) if _skin_rows else ""

    # clocktime
    clock_html = _toggle2("clocktime", s["clocktime"], "/?clocktime=switch", T["countdown"], T["clock_time"], T["time_label"])

    # deviations (SL only)
    devs_html = ""
    if op_code == "SL":
        devs_html = _chk("show_msgs", s["show_msgs"], "/?show_msgs=1", T["t_info"])

    # sleep
    sleep_html = _chk("sleep", s["sleep"], "/?sleep=1", T["turn_off"])

    # button mode
    button_mode_html = ""
    if if_long > 64 and varinit.display.height <= 32:
        button_mode_html = _toggle2("button_mode", s.get("button_mode", 0), "/?button_mode=switch", T["turn_off_short"], T["switch_mode"], T["button_behavior_label"])

    # show station
    show_stn_html = _chk("show_my_station", s["show_my_station"], "/?show_station=1", T["show_station"])

    # LED tone swatches (128-wide boards also get a white option)
    _color_cur = s.get("color", 1)
    def _swatch(value, color, title):
        active = " active" if int(_color_cur) == value else ""
        return ('<button type="button" class="color-swatch-btn' + active + '" style="background:' + color
                + '" title="' + title + '" onclick="setColor(' + str(value) + ',this)"></button>')
    tone_html = _swatch(0, "#e09d00", "Orange") + _swatch(1, "#f5d105", "Yellow")
    if if_long == 128:
        tone_html += _swatch(2, "#ffffff", "White")

    # font size segmented control (mini / small / large)
    _fs = "mini" if s["mini"] else ("large" if s.get("large_list", 0) else "small")
    font_size_html = (
        '<span class="seg">'
        '<button type="button" onclick="setFont(\'mini\',this)" class="' + ("on" if _fs == "mini" else "") + '">mini</button>'
        '<button type="button" onclick="setFont(\'small\',this)" class="' + ("on" if _fs == "small" else "") + '">small</button>'
        '<button type="button" onclick="setFont(\'large\',this)" class="' + ("on" if _fs == "large" else "") + '">large</button>'
        '</span>'
    )
    font_size_row = '<tr><td><b>' + T["font_mini"] + '</b></td><td>' + font_size_html + '</td></tr>' if if_long > 64 else ""
    xs_line_id_chk = _chk("XS_LINE_ID", s.get("xs_line_id", 0), "/?xs_line_id=switch", "Show line ID") if if_long <= 64 else ""
    multi_station_line_id_chk = _chk("MULTI_STATION_LINE_ID", s.get("multi_station_line_id", 0), "/?multi_station_line_id=switch", "Show line ID in multi-line list mode") if if_long > 64 else ""
    clock_row_html = (
        '<tr><td><b>Clock row</b></td><td>' + _chk("SHOW_CLOCK_ROW", s.get("show_clock_row", 0), "/?show_clock_row=switch", "Show date/time instead of a departure") + '</td></tr>'
        '<tr><td><b>Clock: show date</b></td><td>' + _chk("CLOCK_ROW_DATE", s.get("clock_row_date", 0), "/?clock_row_date=switch", "Include date") + '</td></tr>'
        '<tr><td><b>Clock: position</b></td><td><select id="clock_row_position" class="form-control" style="width:130px;display:inline" data-p="clock_row_position" data-e="change">'
        + _opt("bottom", s.get("clock_row_position", "bottom"), "Bottom row")
        + _opt("top", s.get("clock_row_position", "bottom"), "Top row")
        + '</select></td></tr>'
        '<tr><td><b>Clock: align</b></td><td><select id="clock_row_align" class="form-control" style="width:130px;display:inline" data-p="clock_row_align" data-e="change">'
        + _opt("left", s.get("clock_row_align", "left"), "Left")
        + _opt("center", s.get("clock_row_align", "left"), "Center")
        + _opt("right", s.get("clock_row_align", "left"), "Right")
        + '</select></td></tr>'
        '<tr><td><b>Clock: color</b></td><td><select id="clock_row_color" class="form-control" style="width:130px;display:inline" data-p="clock_row_color" data-e="change">'
        + _opt("white", s.get("clock_row_color", "white"), "White")
        + _opt("yellow", s.get("clock_row_color", "white"), "Yellow / amber")
        + _opt("red", s.get("clock_row_color", "white"), "Red")
        + _opt("green", s.get("clock_row_color", "white"), "Green")
        + _opt("blue", s.get("clock_row_color", "white"), "Blue")
        + '</select></td></tr>'
    )
    # dest_scroll
    dest_scroll_html = _chk("DEST_SCROLL", s.get("dest_scroll", 0), "/?dest_scroll=switch", "Scroll long destination names")

    # rt_indicator
    rt_indicator_html = _chk("RT_INDICATOR", s["rt_indicator"], "/?rt_indicator=switch", T["rt_indicator"])
    listcolor_html = _chk("LISTCOLOR", s["listcolor"], "/?listcolor=switch", T["list_colors_line"])
    listcolor_time_html = _chk("LISTCOLOR_TIME", s.get("listcolor_time", 0), "/?listcolor_time=switch", T["list_colors_time"])

    # navbar led toggle: on_off_counter == 0 means display currently off
    led_off_cls = "" if int(varinit.on_off_counter) else " led-off"
    sig_bars = _sig_bars(_rssi(functions))

    # build page using pre-split template (single pass, no scanning)
    _v = {
        "CSS": css, "TITLE": T["title"],
        "HEADER": T["title"],
        "USER_EMAIL": str(s.get("user", "")).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;"),
        "LED_OFF_CLS": led_off_cls,
        "SIG_BARS": sig_bars,
        "IP_DISPLAY": ip,
        "T_WIFI_LABEL": T["network"],
        "SSID_OPTIONS": ssid_opt,
        "NET_DIS": net_dis,
        "T_PASSWORD": T["password"],
        "T_CONNECT": T["connect"],
        "T_ROTATION": T["rotation"],
        "T_POWER": T["power"],
        "POWER_VAL": str(s["power"]),
        "DNS_SECTION": dns_html,
        "T_STATION_DISPLAY": T["station_display"],
        "CURRENT_SKIN": cur_skin,
        "MULTIPLE_SECTION": mult_html,
        "COUNTRY_FLAG": country_flag,
        "OPERATOR": op, "COMBINED_LIST": combined_list,
        "SCREEN_BUTTONS": screen_btns, "SCREEN_BTN_DISP": screen_btn_disp,
        "DISRUPTIONS": disruptions,
        "STATION_PH": station_ph, "SEARCH_DIS": search_dis,
        "T_SEARCH": T["_search"],
        "OPBTN_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (not co or not stn["operator"]) else "",
        "SSTRING_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (co and stn["operator"] and connected and not stn["mystation"]) else "",
        "RESULTS": varinit.results, "RESULT_DIS": result_dis,
        "RESULT_STYLE": result_style,
        "T_NO_DEPARTURES": T["no_departures"],
        "MAXDEST_OPTIONS": maxdest_opt,
        "METRO_SECTION": metro_html, "SL_SECTION": sl_section,
        "BUS_SECTION": bus_html,
        "TRAIN_CHK": train_html, "TRAM_SECTION": tram_html,
        "SHIP_SECTION": ship_html,
        "T_HIDE_DEPARTURES": T["hide_departures"],
        "OFFSET_OPTIONS": offset_opt,
        "DIRECTION_SECTION": dir_html,
        "SCROLL_SECTION": scroll_html,
        "T_TRAFFIC_TYPES": T["traffic_types"],
        "SKIN_SECTION": skin_html, "CLOCKTIME_CHK": clock_html,
        "DLR_SETTINGS_SECTION": dlr_settings_html,
        "VBZ_SETTINGS_SECTION": vbz_settings_html,
        "UBAHN_SETTINGS_SECTION": ubahn_settings_html,
        "OPERATOR_PICKER_DISP": operator_picker_disp,
        "DSA_PROVIDER_SECTION": dsa_provider_html,
        "SKIN_DELETE_SECTION": skin_delete_html,
        "DEVIATIONS_SECTION": devs_html,
        "SLEEP_CHK": sleep_html, "BUTTON_MODE_CHK": button_mode_html, "SHOW_STATION_CHK": show_stn_html,
        "T_SAVE": T["save"],
        "T_ADVANCED": T["advanced"],
        "T_TONE": T["tone"], "TONE_SWATCHES": tone_html,
        "FONT_SIZE_ROW": font_size_row,
        "XS_LINE_ID_CHK": xs_line_id_chk,
        "MULTI_STATION_LINE_ID_CHK": multi_station_line_id_chk,
        "DEST_SCROLL_CHK": dest_scroll_html,
        "RT_INDICATOR_CHK": rt_indicator_html,
        "LISTCOLOR_CHK": listcolor_html,
        "LISTCOLOR_TIME_CHK": listcolor_time_html,
        "CLOCK_ROW_HTML": clock_row_html,
        "T_LINE_LENGTH": T["line_length"],
        "T_LINE_LENGTH_HELP": "Most line numbers are 1-2 characters, so this often looks the same until a line uses a longer code.",
        "LINE_LENGTH_VAL": str(s["line_length"]),
        "T_SHOW_LINES": T["show_lines"],
        "SHOW_LINES_VAL": ",".join(s["show_lines"]) if isinstance(s["show_lines"], list) else str(s["show_lines"]),
        "STRIP_DEST_VAL": ",".join(s.get("strip_dest", [])) if isinstance(s.get("strip_dest"), list) else str(s.get("strip_dest", "")),
        "DEST_ABBREV_VAL": ",".join([p[0] + "=" + p[1] for p in s.get("dest_abbrev", []) if isinstance(p, list) and len(p) == 2]) if isinstance(s.get("dest_abbrev"), list) else str(s.get("dest_abbrev", "")),
        "T_NO_MORE_DEP": T["no_more_departures_label"],
        "NO_MORE_DEP_VAL": str(s["no_more_departures"]),
        "T_MINS": T["mins_label"],
        "MINS_VAL": str(s["mins"]),
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
        except: timer[i] = ["00:00", "00:00"]
    T = language[_language]["settings"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rows = ""
    for day in days:
        label = T[day.lower()]
        did = day.lower()
        rows += ('<div class="form-row" style="align-items:center;margin-bottom:8px">'
                 '<div class="col" style="flex:0 0 90px;text-transform:capitalize;font-size:.85rem">' + label + '</div>'
                 '<div class="col"><input type="time" id="' + did + 'S" class="form-control" value="' + timer[day][0] + '"></div>'
                 '<div class="col"><input type="time" id="' + did + 'E" class="form-control" value="' + timer[day][1] + '"></div>'
                 '</div>'
                 '<script>(function(){var s=document.getElementById("' + did + 'S"),e=document.getElementById("' + did + 'E");'
                 'function send(){if(s.value&&e.value)fetch("/?set_timer=' + day + '&start="+encodeURIComponent(s.value+"to="+e.value),{method:"GET"})}'
                 's.addEventListener("change",send);e.addEventListener("change",send);})()</script>')
    body = ('<div class="card"><div class="section-title">' + T["timer_title"] + '</div>' + rows
            + '<button type="button" class="btn btn-full btn-ghost" onclick="location.href=\'/\'">' + T["return"] + '</button>'
            + '<button type="button" class="btn btn-full btn-danger" onclick="location.href=\'/?cleartimer=true\'">' + T["clear"] + '</button></div>')
    return ('<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">'
            '<title>' + T["timer_title"] + '</title><style>' + css + '</style></head>'
            '<body><nav class="navbar"><a class="nav-x" href="/" title="Back" style="margin-left:0">&#8592;</a>'
            '<span class="nav-title">' + T["timer_title"] + '</span></nav><div class="page">' + body + '</div></body></html>')
