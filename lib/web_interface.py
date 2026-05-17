from fetch_data import fetch
#from load_settings import savesettings
from __main__ import *
import __main__
#from main import connect_to_network
#import __main__
#print(dir(__main__))

_FAVICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><filter id="led-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="0.7" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="32" height="32" rx="5" fill="#0d0d0d"/><rect x="0.5" y="0.5" width="31" height="31" rx="4.5" fill="none" stroke="#2a2a2a" stroke-width="1"/><circle cx="6" cy="6" r="1.8" fill="#1c1c1c"/><circle cx="11" cy="6" r="1.8" fill="#1c1c1c"/><circle cx="16" cy="6" r="1.8" fill="#1c1c1c"/><circle cx="21" cy="6" r="1.8" fill="#1c1c1c"/><circle cx="26" cy="6" r="1.8" fill="#1c1c1c"/><circle cx="6" cy="11" r="1.8" fill="#1c1c1c"/><circle cx="11" cy="11" r="1.8" fill="#1c1c1c"/><circle cx="16" cy="11" r="1.8" fill="#1c1c1c"/><circle cx="21" cy="11" r="1.8" fill="#1c1c1c"/><circle cx="26" cy="11" r="1.8" fill="#1c1c1c"/><circle cx="6" cy="16" r="1.8" fill="#1c1c1c"/><circle cx="11" cy="16" r="1.8" fill="#1c1c1c"/><circle cx="16" cy="16" r="1.8" fill="#1c1c1c"/><circle cx="21" cy="16" r="1.8" fill="#1c1c1c"/><circle cx="26" cy="16" r="1.8" fill="#1c1c1c"/><circle cx="6" cy="21" r="1.8" fill="#1c1c1c"/><circle cx="11" cy="21" r="1.8" fill="#1c1c1c"/><circle cx="16" cy="21" r="1.8" fill="#1c1c1c"/><circle cx="21" cy="21" r="1.8" fill="#1c1c1c"/><circle cx="26" cy="21" r="1.8" fill="#1c1c1c"/><circle cx="6" cy="26" r="1.8" fill="#1c1c1c"/><circle cx="11" cy="26" r="1.8" fill="#1c1c1c"/><circle cx="16" cy="26" r="1.8" fill="#1c1c1c"/><circle cx="21" cy="26" r="1.8" fill="#1c1c1c"/><circle cx="26" cy="26" r="1.8" fill="#1c1c1c"/><circle cx="6" cy="6" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="26" cy="6" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="6" cy="11" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="11" cy="11" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="21" cy="11" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="26" cy="11" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="6" cy="16" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="16" cy="16" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="26" cy="16" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="6" cy="21" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="26" cy="21" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="6" cy="26" r="1.8" fill="#ffc800" filter="url(#led-glow)"/><circle cx="26" cy="26" r="1.8" fill="#ffc800" filter="url(#led-glow)"/></svg>'
exitbutton = """<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><link rel="icon" type="image/svg+xml" href="/favicon.svg"><style>body{background:#08080f;color:#eeeef5;font-family:system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;gap:16px;margin:0}a.xbtn{display:inline-flex;align-items:center;gap:8px;padding:12px 28px;border-radius:10px;background:linear-gradient(135deg,#e03c3c,#ff6060);color:#fff;font-weight:700;font-size:.95rem;text-decoration:none;box-shadow:0 2px 14px rgba(224,60,60,.35)}.lbl{color:#7070a0;font-size:.75rem;text-transform:uppercase;letter-spacing:1.5px}</style></head><body><p class="lbl">App Running</p><a class="xbtn" href="/exit">&#x2715; Exit App</a>"""
backbutton = """<a class="back-btn" href="../">&#8592; Back</a>"""
bootloaderbutton = """<button class="btn btn-danger" onclick="if(confirm('Enter bootloader mode?'))fetch('/bootloader',{method:'POST'})">&#x26A1; Bootloader</button>"""
#unlock = """<button class="center" onclick="window.location.href='/unlock'" style='background-color:yellow'> &#128275; </button>"""
unlock = """<button class="btn btn-warning" onclick="fetch('/?unlock=true', {method: 'POST'})">&#x1F513; Unlock</button>"""

# -- LED on/off toggle ---------------------------------------------------------
_led_off = False

def _led_toggle():
    global _led_off
    _led_off = not _led_off
    display.root_group.hidden = _led_off
    refresh()
    return _led_off

def _get_installed_apps():
    apps = []
    for app in os.listdir("/"):
        if app == "LICENSE": continue
        if not "." in app:
            try:
                if not "__init__.py" in os.listdir("/" + app): continue
            except: continue
            apps.append(app)
    return apps

def _app_ver(path):
    try:
        for f in os.listdir(path):
            if f[0] == "v" and f[1:2].isdigit(): return f[1:]
    except: pass
    return ""

def _dir_size(path):
    total = 0
    try:
        for f in os.listdir(path):
            fp = path + "/" + f
            try:
                s = os.stat(fp)
                if s[0] & 0x4000:  # directory
                    total += _dir_size(fp)
                else:
                    total += s[6]
            except: pass
    except: pass
    return total

def _fmt_size(b):
    if b < 1024: return str(b) + " B"
    elif b < 1024*1024: return str(b // 1024) + " KB"
    else: return "{:.1f} MB".format(b / (1024*1024))

def _free_space():
    s = os.statvfs("/")
    return s[0] * s[3]  # block size * free blocks

def textbox(settings):
    slider_cfg = {
        "wifi_power": {"min": 7, "max": 20, "step": 1},
        "rotation": {"min": 0, "max": 270, "step": 90},
        "width": {"min": 64, "max": 640, "step": 64},
        "height": {"min": 32, "max": 320, "step": 32},
    }
    hidden_keys = {"ai_provider", "ai_key", "ai_model", "repository_file"}
    advanced_keys = {"width", "height", "tiles", "repository_url"}
    advanced_order = ["width", "height", "tiles", "repository_url"]
    wifi_group = {}
    app_group = []
    main_html = ""
    adv_items = {}
    settings_html = """<form onsubmit="sav(event)">"""
    for setting in settings:
        if setting in hidden_keys: continue
        print("Setting: ", setting)
        val = settings[setting]
        is_adv = setting in advanced_keys
        chunk = ""
        if setting == "autostart":
            apps = _get_installed_apps()
            checked = "checked" if val else ""
            disabled = "" if val else "disabled"
            opts = ""
            for a in apps:
                sel = "selected" if str(val) == a else ""
                opts += f'<option value="{a}" {sel}>{a}</option>'
            chunk = f"""<label>{setting}</label>
<div class="toggle-row">
<input type="checkbox" id="as_chk" {checked} onchange="var s=document.getElementById('as_sel');var h=document.getElementById('autostart');s.disabled=!this.checked;if(!this.checked){{s.value='';h.value='';}}">
<label for="as_chk">Enable autostart</label>
</div>
<input type="hidden" id="autostart" name="autostart" value="{val if val else ''}">
<select id="as_sel" {disabled} onchange="document.getElementById('autostart').value=this.value"><option value="">-- none --</option>{opts}</select>"""
        elif setting == "screensaver":
            apps = _get_installed_apps()
            checked = "checked" if val else ""
            disabled = "" if val else "disabled"
            opts = ""
            for a in apps:
                sel = "selected" if str(val) == a else ""
                opts += f'<option value="{a}" {sel}>{a}</option>'
            chunk = f"""<label>{setting}</label>
<div class="toggle-row">
<input type="checkbox" id="ss_chk" {checked} onchange="var s=document.getElementById('ss_sel');var h=document.getElementById('screensaver');s.disabled=!this.checked;if(!this.checked){{s.value='';h.value='';}}">
<label for="ss_chk">Enable screensaver</label>
</div>
<input type="hidden" id="screensaver" name="screensaver" value="{val if val else ''}">
<select id="ss_sel" {disabled} onchange="document.getElementById('screensaver').value=this.value"><option value="">-- none --</option>{opts}</select>"""
        elif setting in slider_cfg:
            c = slider_cfg[setting]
            try: cur = int(float(val))
            except: cur = c["min"]
            if setting == "rotation":
                chunk = f"""<label>{setting}</label>
<div class="range-wrap">
<input type="range" id="{setting}" name="{setting}" min="{c['min']}" max="{c['max']}" step="{c['step']}" value="{cur}" oninput="document.getElementById('v_{setting}').textContent=this.value" onchange="fetch('/rotate?v='+this.value,{{method:'POST'}})">
<span class="range-val" id="v_{setting}">{cur}</span>
</div>"""
            else:
                chunk = f"""<label>{setting}</label>
<div class="range-wrap">
<input type="range" id="{setting}" name="{setting}" min="{c['min']}" max="{c['max']}" step="{c['step']}" value="{cur}" oninput="document.getElementById('v_{setting}').textContent=this.value">
<span class="range-val" id="v_{setting}">{cur}</span>
</div>"""
        else:
            chunk = f"""<label for="{setting}">{setting}</label>
<input type="text" id="{setting}" name="{setting}" placeholder="{str(val)}">"""
        if is_adv:
            adv_items[setting] = chunk
        elif setting in ("ssid", "password"):
            wifi_group[setting] = chunk
        elif setting in ("autostart", "screensaver"):
            app_group.append(chunk)
        else:
            main_html += chunk
    wifi_html = ""
    if wifi_group:
        ordered = "".join(wifi_group.get(k, "") for k in ["ssid", "password"])
        wifi_html = '<div class="section-title" style="margin-top:12px">Wi-Fi</div>' + ordered
    app_html = ""
    if app_group:
        app_html = '<div class="section-title" style="margin-top:12px">App Behavior</div>' + "".join(app_group)
    settings_html += wifi_html + main_html + app_html
    adv_html = "".join(adv_items[k] for k in advanced_order if k in adv_items)
    if adv_html:
        settings_html += """<div style="margin-top:12px"><button type="button" class="btn btn-sm" onclick="var a=document.getElementById('adv_section');a.style.display=a.style.display==='none'?'block':'none'">&#9881; Advanced</button></div><div id="adv_section" style="display:none">""" + adv_html + """</div>"""
    return settings_html + """<button class="btn btn-full btn-success" type="submit">Save Settings</button></form>"""
    
def _draw_progress(current, total, filename, error=False, label="installing"):
    from load_screen import window, pset, font_mini
    w = display.width
    h = display.height
    window.fill(0)
    # Draw filename on line 1 first (line=1 does NOT auto-refresh)
    name = filename.split("/")[-1]
    pprint(name, 1, _clearscreen=False, color="yellow" if not error else "red")
    # Draw progress bar (no refresh yet)
    bar_h = 4
    bar_y = h - bar_h - 9
    bar_x = 1
    bar_w = w - 2
    for px in range(bar_x, bar_x + bar_w):
        pset(px, bar_y, 5)
        pset(px, bar_y + bar_h, 5)
    for py in range(bar_y, bar_y + bar_h + 1):
        pset(bar_x, py, 5)
        pset(bar_x + bar_w - 1, py, 5)
    fill_w = int((bar_w - 2) * current / max(total, 1))
    for px in range(bar_x + 1, bar_x + 1 + fill_w):
        for py in range(bar_y + 1, bar_y + bar_h):
            pset(px, py, 7)
    # Draw label on line 0 LAST (line=0 auto-refreshes, showing complete frame)
    pprint(label + " " + str(current) + "/" + str(total), 0, _clearscreen=False)

def install_app(app):
    if app == "system": app = "/"
    print("Install: ", app)
    applist = load_settings.latest_available_apps
    no_of_files = len(applist[app])
    print("Applist: ", applist, " Files: ", no_of_files)
    os.chdir("/")
    if app != "/":
        try: os.mkdir(app)
        except: pass
        try: os.chdir(app)
        except: pass
    error_color = "green"
    from load_screen import window
    try:
        try: microcontroller.cpu.frequency = 240000000
        except: pass
        clearscreen(False)
        # Pass 1: download all files, verify each returns 200
        downloads = []
        for x, file in enumerate(applist[app]):
            if "/" in file:
                parts = file.split("/")[:-1]
                path = ""
                for part in parts:
                    path = path + "/" + part if path else part
                    try: os.mkdir(path)
                    except: pass
            print("File: ", file)
            file_url = settings["repository_url"]
            if app != "/":
                file_url += "apps/" + app + "/"
            _draw_progress(x, no_of_files, file)
            resp = requests.get(file_url + file)
            print(resp.status_code)
            if resp.status_code != 200:
                _draw_progress(x + 1, no_of_files, file, True)
                try: resp.close()
                except: pass
                pprint("http " + str(resp.status_code), color="red", line=-1, _refresh=True)
                return
            if file.rsplit(".", 1)[-1] in ("mpy", "gif", "bmp", "png", "jpg", "bin", "raw"):
                downloads.append((file, bytearray(resp.content), "wb"))
            else:
                downloads.append((file, resp.text, "w"))
            _draw_progress(x + 1, no_of_files, file)
        # Pass 2: all downloads OK, write to disk
        window.fill(0)
        display.refresh()
        for fname, data, mode in downloads:
            try:
                with open(str(fname), mode) as f: f.write(data)
            except:
                error_color = "red"
        downloads = None
        #gc.collect()
    finally:
        try: microcontroller.cpu.frequency = 180000000
        except: pass
        os.chdir("/")
        # Update cached version: local now matches remote
        try:
            r_vers = getattr(load_settings, 'remote_versions', {})
            if app == "/":
                r_ver = r_vers.get("/", "")
                if r_ver:
                    # Remove old local version file, keep new one
                    for f in os.listdir("lib"):
                        if f[0] == "v" and f[1:2].isdigit() and f[1:] != r_ver:
                            try: os.remove("lib/" + f)
                            except: pass
            else:
                r_ver = r_vers.get(app, "")
                if r_ver:
                    for f in os.listdir(app):
                        if f[0] == "v" and f[1:2].isdigit() and f[1:] != r_ver:
                            try: os.remove(app + "/" + f)
                            except: pass
        except: pass
        window.fill(0)
        pprint("Done.", 1, _clearscreen=True)
        if app == "/":
            try:
                with open("reboot_required", "w") as f: f.write("")
            except OSError: pass
        __main__.show_logo()
        


def _repo_api_base():
    """Derive GitHub API repo path from repository_url.
    e.g. 'https://raw.githubusercontent.com/matrixbox/matrixbox/refs/heads/main/'
    -> owner='matrixbox', repo='matrixbox'
    """
    url = settings["repository_url"]
    parts = url.replace("https://", "").split("/")
    return parts[1], parts[2]

_cached_apps = None

def get_updates(force=False):
    global _cached_apps
    if _cached_apps is not None and not force:
        return _cached_apps
    print(settings)
    try:
        owner, repo = _repo_api_base()
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        resp = requests.get(url, headers={"User-Agent": "MatrixBox"}, timeout=10)
        tree = json.loads(resp.text)["tree"]
        resp.close()
        apps = {}
        root_files = []
        for item in tree:
            if item["type"] != "blob": continue
            path = item["path"]
            parts = path.split("/")
            if len(parts) == 1:
                root_files.append(parts[0])
                continue
            if parts[0] == "apps" and len(parts) > 2:
                dirname = parts[1]
                filename = "/".join(parts[2:])
            elif parts[0] == "lib":
                dirname = parts[0]
                filename = "/".join(parts[1:])
            else:
                continue
            if dirname not in apps: apps[dirname] = []
            apps[dirname].append(filename)
        # System = root files + lib folder
        system_files = root_files[:]
        if "lib" in apps:
            for f in apps["lib"]:
                system_files.append("lib/" + f)
        apps["/"] = system_files
        # Keep only dirs with __init__.py, "lib", or root "/"
        apps = {k: v for k, v in apps.items() if k in ("/", "lib") or "__init__.py" in v}
        # Extract remote versions from version files
        _remote_vers = {}
        for k, files in apps.items():
            for f in files:
                fn = f.split("/")[-1]
                if fn[0:1] == "v" and fn[1:2].isdigit():
                    _remote_vers[k] = fn[1:]
                    break
        load_settings.remote_versions = _remote_vers
        _cached_apps = apps
    except Exception as e:
        print("get_updates error:", e)
        apps = _cached_apps if _cached_apps else {}
    return apps
    
def list_available_apps(apps):
    print("Apps: ", apps)
    load_settings.latest_available_apps = apps
    remote_vers = getattr(load_settings, 'remote_versions', {})
    sys_l = _app_ver("lib")
    sys_r = remote_vers.get("/", "")
    sys_ver = 'v' + sys_l if sys_l else 'system'
    if sys_r and sys_l and sys_r != sys_l:
        sys_ver += ' &#x2192; v' + sys_r
        sys_btn = '<button class="btn btn-sm" style="background:linear-gradient(135deg,#00c85d,#00e676);color:#000;border:2px solid #f0c800" onclick="installsystem(event)">&#x21BB; Update</button>'
    else:
        sys_btn = '<button class="btn btn-sm btn-warning" onclick="installsystem(event)">&#x21BB; Reinstall</button>'
    applist = '<div class="download-item"><div><span class="download-name">&#x1F4E6; System</span><div style="font-size:.7rem;color:#f0c800;margin-top:2px">' + sys_ver + '</div></div>' + sys_btn + """\n    <script>function _busyWait(url,btn){
    var old=btn.innerHTML;btn.disabled=true;btn.innerHTML='<span style="display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite"></span>';
    var w=document.createElement('div');w.className='busy-warn';w.textContent='\u26A0 Writing to disk \u2014 do not turn off!';document.body.appendChild(w);
    fetch(url,{method:"POST"}).then(function(){w.remove();nav('/f/download')}).catch(function(){w.remove();btn.innerHTML=old;btn.disabled=false});}
    function installsystem(e){_busyWait("/?install=system",e.currentTarget)}</script></div>"""

    for dir in apps:
        if dir == "/" or dir == "lib": continue
        r_ver = remote_vers.get(dir, "")
        if dir in os.listdir() and "__init__.py" in os.listdir(dir):
            sz = _fmt_size(_dir_size(dir))
            l_ver = _app_ver(dir)
            ver_info = 'v' + l_ver if l_ver else sz
            if r_ver and l_ver and r_ver != l_ver:
                ver_info += ' &#x2192; v' + r_ver
                upd_btn = '<button class="btn btn-sm" style="background:linear-gradient(135deg,#00c85d,#00e676);color:#000;border:2px solid #f0c800" onclick="install'+dir+'(event)">&#x21BB; Update</button>'
            else:
                upd_btn = '<button class="btn btn-sm btn-warning" onclick="install'+dir+'(event)">&#x21BB; Reinstall</button>'
            applist += f'<div class="download-item"><div><span class="download-name">&#x2713; {dir}</span><div style="font-size:.7rem;color:#f0c800;margin-top:2px">{ver_info}</div></div><div style="display:flex;gap:6px">' + upd_btn + """<button class="btn btn-sm" style="background:#ff4b4b;color:#fff;padding:7px 9px" onclick="if(confirm('Delete """+dir+"""?'))del"""+dir+"""(event)">&#x2715;</button>
<script>function install"""+dir+"""(e){_busyWait("/?install="""+dir+"""",e.currentTarget)}
function del"""+dir+"""(e){_busyWait("/?delete="""+dir+"""",e.currentTarget)}</script></div></div>"""
        else:
            ver_label = f'{dir} <span style="color:#f0c800">v{r_ver}</span>' if r_ver else dir
            applist += f'<div class="download-item"><span class="download-name">{ver_label}</span>' + """<button class="btn btn-sm btn-success" onclick="install"""+dir+"""(event)">&#x2B07; Install</button>
<script>function install"""+dir+"""(e){_busyWait("/?install="""+dir+"""",e.currentTarget)}</script></div>"""
    return applist


def latest_wifi_error():
    return str(__main__.wifi_status)

def css():
    return """
:root{--bg:#08080f;--surface:#111118;--surface2:#1c1c2a;--surface3:#26263a;--accent:#7c6fff;--accent2:#00d4ff;--text:#eeeef5;--muted:#7070a0;--border:rgba(120,120,255,.1);--r:10px;--r-lg:16px;--shadow:0 4px 24px rgba(0,0,0,.5)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;min-height:100vh;padding-bottom:40px}
.navbar{position:sticky;top:0;z-index:100;background:rgba(8,8,15,.85);border-bottom:1px solid var(--border);padding:0 14px;display:flex;align-items:center;height:46px;gap:4px;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.nav-brand{font-weight:800;font-size:.9rem;color:#fff;margin-right:6px;text-decoration:none;letter-spacing:-.2px}
.nav-title{font-weight:600;font-size:.9rem;color:var(--text);flex:1;padding-left:4px}
.nav-link{color:var(--muted);text-decoration:none;font-size:.76rem;padding:5px 9px;border-radius:7px;transition:color .15s,background .15s;font-weight:500}
.nav-link:hover{color:var(--text);background:var(--surface2)}
.nav-spacer{flex:1}
.nav-info{color:var(--muted);font-size:.68rem;letter-spacing:.2px;text-align:right;line-height:1.4}
.nav-info span{display:block}
.sig{display:flex;align-items:center;gap:2px;margin:0 6px}
.sig i{display:block;width:5px;height:5px;background:rgba(112,112,160,.3);border-radius:1px}
.sig i.on{background:#00c853}
.nav-x{color:var(--muted);font-size:1rem;font-weight:700;text-decoration:none;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);transition:color .15s,border-color .15s,background .15s;margin-left:4px}
.nav-x:hover{color:#ff6060;border-color:rgba(255,96,96,.4);background:rgba(255,96,96,.08)}
.nav-led{color:var(--muted);font-size:.85rem;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);transition:color .15s,border-color .15s,background .15s;margin-left:4px;cursor:pointer;background:none}
.nav-led:hover{color:#ffd060;border-color:rgba(255,208,96,.4);background:rgba(255,208,96,.08)}
.nav-led.led-off{color:#ff4040;border-color:rgba(255,64,64,.35);background:rgba(255,64,64,.06)}
.page{max-width:480px;margin:0 auto;padding:16px 14px}
.logo{text-align:center;padding:26px 0 18px}
.logo h1{font-size:1.8rem;font-weight:800;color:#fff;letter-spacing:-.5px}
.logo p{color:var(--muted);font-size:.82rem;margin-top:6px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:16px;margin-bottom:10px;box-shadow:var(--shadow)}
.section-title{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.4px;font-weight:700;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.app-item,.download-item{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border)}
.app-item:last-child,.download-item:last-child{border-bottom:none}
.app-name{font-size:.92rem;font-weight:500;text-transform:capitalize;color:var(--text)}
.download-name{font-size:.92rem;font-weight:500;color:var(--text)}
label{display:block;font-size:.67rem;color:var(--muted);text-transform:uppercase;letter-spacing:.9px;margin:13px 0 5px;font-weight:600}
input[type="text"],select{width:100%;background:var(--surface2);border:1.5px solid var(--border);border-radius:var(--r);padding:10px 12px;color:var(--text);font-size:.93rem;outline:none;transition:border-color .15s,box-shadow .15s;-webkit-appearance:none}
input[type="text"]:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,111,255,.15)}
select option{background:var(--surface2)}
.range-wrap{display:flex;align-items:center;gap:10px;margin-top:5px}
.range-wrap input[type="range"]{flex:1;-webkit-appearance:none;appearance:none;height:5px;border-radius:3px;background:var(--surface3);outline:none}
.range-wrap input[type="range"]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:linear-gradient(135deg,#c8a800,#f5e040);cursor:pointer;border:2px solid var(--bg);box-shadow:0 2px 8px rgba(232,150,14,.4)}
.range-val{min-width:34px;text-align:center;font-size:.85rem;font-weight:700;color:#f0c800;background:var(--surface2);padding:3px 7px;border-radius:7px}
.toggle-row{display:flex;align-items:center;gap:10px;margin:10px 0}
.toggle-row input[type="checkbox"]{width:18px;height:18px;accent-color:var(--accent)}
.toggle-row label{margin:0;font-size:.85rem;color:var(--text);text-transform:none;letter-spacing:0;font-weight:500}
.sw{position:relative;display:inline-block;width:44px;height:24px;flex-shrink:0}
.sw input{opacity:0;width:0;height:0;position:absolute}
.sl{position:absolute;cursor:pointer;inset:0;background:var(--surface3);border-radius:24px;transition:.2s;border:1px solid var(--border)}
.sl:before{content:"";position:absolute;height:18px;width:18px;left:2px;bottom:2px;background:var(--muted);border-radius:50%;transition:.2s}
.sw input:checked+.sl{background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:transparent}
.sw input:checked+.sl:before{transform:translateX(20px);background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.4)}
.toggle-item{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border)}
.toggle-item:last-child{border-bottom:none}
.toggle-item span{font-size:.9rem;color:var(--text)}
.swatch-row{display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap}
.color-swatch{width:26px;height:26px;border-radius:7px;border:2px solid var(--border);cursor:pointer;transition:transform .1s,border-color .1s}
.color-swatch:hover,.color-swatch.active{transform:scale(1.15);border-color:rgba(255,255,255,.6)}
input[type="color"]{width:36px;height:36px;border:2px solid var(--border);border-radius:8px;background:var(--surface2);cursor:pointer;padding:2px;-webkit-appearance:none}
input[type="color"]::-webkit-color-swatch-wrapper{padding:0;border-radius:5px}
input[type="color"]::-webkit-color-swatch{border:none;border-radius:5px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:9px 18px;border:none;border-radius:var(--r);font-size:.86rem;font-weight:600;cursor:pointer;transition:opacity .15s,transform .1s,box-shadow .15s;color:#111;background:linear-gradient(135deg,#c8a800,#f5e040);text-decoration:none;box-shadow:0 2px 12px rgba(200,168,0,.35)}
.btn:hover{opacity:.88;transform:translateY(-1px);box-shadow:0 4px 16px rgba(124,111,255,.4)}
.btn:active{transform:translateY(0);opacity:1;box-shadow:none}
.btn-sm{padding:6px 12px;font-size:.8rem}
.btn-full{width:100%;padding:12px;font-size:.93rem;margin-top:10px}
.btn-danger{background:linear-gradient(135deg,#e03c3c,#ff6060);color:#fff;box-shadow:0 2px 12px rgba(224,60,60,.3)}
.btn-success{background:linear-gradient(135deg,#00b050,#00e676);color:#000;box-shadow:0 2px 12px rgba(0,176,80,.3)}
.btn-warning{background:linear-gradient(135deg,#c8a800,#f5e040);color:#111;box-shadow:0 2px 12px rgba(200,168,0,.35)}
.btn-ghost{background:var(--surface2);border:1px solid var(--border);color:var(--text);box-shadow:none}
.btn-ghost:hover{border-color:var(--accent);background:var(--surface3)}
.seg{display:flex;background:var(--surface2);border-radius:var(--r);padding:3px;gap:2px;border:1px solid var(--border)}
.seg button{flex:1;padding:6px 10px;border:none;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;background:none;color:var(--muted);transition:all .15s}
.seg button.on{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;box-shadow:0 2px 8px rgba(124,111,255,.3)}
.action-row{display:flex;gap:8px;flex-wrap:wrap}.action-row-fill{flex-wrap:nowrap}.action-row-fill .btn{flex:1;min-width:0;padding-left:4px;padding-right:4px;justify-content:center;text-align:center}
.back-btn{display:inline-flex;align-items:center;gap:6px;color:var(--muted);text-decoration:none;font-size:.83rem;padding:8px 13px;border-radius:var(--r);background:var(--surface);border:1px solid var(--border);margin-top:14px;transition:color .15s,border-color .15s}
.back-btn:hover{color:var(--text);border-color:var(--accent)}
.error-msg{color:#ff7070;font-size:.82rem;margin-top:10px;text-align:center}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes reboot-blink{0%,100%{color:#ff6060;border-color:rgba(255,96,96,.7);background:rgba(255,96,96,.15)}50%{color:var(--muted);border-color:var(--border);background:transparent}}
.nav-x.reboot-needed{animation:reboot-blink 1s ease-in-out infinite}
.busy-warn{position:fixed;top:46px;left:0;right:0;background:linear-gradient(90deg,#c8a800,#f5e040);color:#111;text-align:center;font-weight:700;font-size:.86rem;padding:10px;z-index:200;letter-spacing:.3px}
"""

def _rssi():
    try:
        ai = wifi.radio.ap_info
        return ai.rssi if ai else -100
    except:
        return -100

def _sig_bars(rssi):
    n = 5 if rssi > -45 else 4 if rssi > -55 else 3 if rssi > -65 else 2 if rssi > -75 else 1 if rssi > -85 else 0
    bars = ''.join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(5))
    return f'<span class="sig" id="sig" title="{rssi} dBm">{bars}</span>'

def navbar():
    ip = str(wifi.radio.ipv4_address) if wifi.radio.ipv4_address else "OFFLINE"
    rssi = _rssi()
    try:
        with open("reboot_required"): _reboot_cls = " reboot-needed"
    except OSError: _reboot_cls = ""
    return f"""<nav class="navbar">
<a class="nav-brand" href="/" onclick="nav('/f/apps');return false">Matrix<span style="color:#f0c800;font-weight:900">BOX</span></a>
<a class="nav-link" href="/download" onclick="nav('/f/download');return false">Store</a>
<a class="nav-link" href="/settings" onclick="nav('/f/settings');return false">Settings</a>
<div class="nav-spacer"></div>
<div class="nav-info"><span id="clk"></span><span>{ip}</span></div>
{_sig_bars(rssi)}
<button class="nav-led{' led-off' if _led_off else ''}" id="ledbtn" onclick="fetch('/led',{{method:'POST'}}).then(function(r){{return r.json()}}).then(function(j){{var b=document.getElementById('ledbtn');if(j.off){{b.classList.add('led-off')}}else{{b.classList.remove('led-off')}}}})" title="Toggle LED">&#x1F4A1;</button>
<button class="nav-x{_reboot_cls}" onclick="if(confirm('Restart?'))fetch('/reset',{{method:'POST'}})" title="Restart">&#x2715;</button>
</nav>
<script>function _ck(){{var d=new Date(),h=d.getHours(),m=d.getMinutes();document.getElementById('clk').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}}_ck();setInterval(_ck,15000);
function _rs(){{fetch('/f/rssi').then(function(r){{return r.text()}}).then(function(v){{var s=document.getElementById('sig');if(!s)return;var r=parseInt(v),n=r>-45?5:r>-55?4:r>-65?3:r>-75?2:r>-85?1:0;s.title=r+' dBm';var b=s.querySelectorAll('i');for(var i=0;i<b.length;i++){{if(i<n)b[i].classList.add('on');else b[i].classList.remove('on');}}}}).catch(function(){{}});}}_rs();setInterval(_rs,30000);</script>"""

def app_navbar(title):
    ip = str(wifi.radio.ipv4_address) if wifi.radio.ipv4_address else "OFFLINE"
    rssi = _rssi()
    return f"""<nav class="navbar">
<a class="nav-x" href="/exit" title="Exit" style="margin-left:0;margin-right:4px">&#8592;</a>
<span class="nav-title">{title}</span>
<div class="nav-spacer"></div>
<div class="nav-info"><span id="clk"></span><span>{ip}</span></div>
{_sig_bars(rssi)}
<button class="nav-led{' led-off' if _led_off else ''}" id="ledbtn" onclick="fetch('/led',{{method:'POST'}}).then(function(r){{return r.json()}}).then(function(j){{var b=document.getElementById('ledbtn');if(j.off){{b.classList.add('led-off')}}else{{b.classList.remove('led-off')}}}})" title="Toggle LED">&#x1F4A1;</button>
<a class="nav-x" href="/exit" title="Exit">&#x2715;</a>
</nav>
<script>function _ck(){{var d=new Date(),h=d.getHours(),m=d.getMinutes();document.getElementById('clk').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}}_ck();setInterval(_ck,15000);
function _rs(){{fetch('/f/rssi').then(function(r){{return r.text()}}).then(function(v){{var s=document.getElementById('sig');if(!s)return;var r=parseInt(v),n=r>-45?5:r>-55?4:r>-65?3:r>-75?2:r>-85?1:0;s.title=r+' dBm';var b=s.querySelectorAll('i');for(var i=0;i<b.length;i++){{if(i<n)b[i].classList.add('on');else b[i].classList.remove('on');}}}}).catch(function(){{}});}}_rs();setInterval(_rs,30000);</script>"""

def header(title="Settings", app=False):
    nav = app_navbar(title) if app else navbar()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <title>{title}</title>
    <style>{css()}</style>
</head>
<body>{nav}<div class="page">"""

def footer(back=False):
    back_html = backbutton if back else ""
    return f"""{back_html}</div></body></html>"""

def _shell(content, title="MatrixBox", frag="/f/apps"):
    nav = navbar()
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<title>{title}</title>
<style>{css()}</style>
</head>
<body>{nav}<div class="page" id="content">{content}</div>
<script>
function _run(c){{var sc=c.querySelectorAll('script');for(var i=0;i<sc.length;i++){{var n=document.createElement('script');n.textContent=sc[i].textContent;document.head.appendChild(n)}}}}
function nav(u){{var c=document.getElementById('content');c.innerHTML='<div style="display:flex;justify-content:center;padding:60px 0"><span style="display:inline-block;width:28px;height:28px;border:3px solid var(--surface3);border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite"></span></div>';fetch(u).then(function(r){{return r.text()}}).then(function(h){{c.innerHTML=h;_run(c);var p=u.replace('/f/apps','/').replace('/f/','/');history.pushState({{f:u}},'',p);window.scrollTo(0,0)}})}}
window.addEventListener('popstate',function(e){{var u=e.state&&e.state.f||'{frag}';fetch(u).then(function(r){{return r.text()}}).then(function(h){{var c=document.getElementById('content');c.innerHTML=h;_run(c)}})}});
history.replaceState({{f:'{frag}'}},'');
function sav(e){{e.preventDefault();var b=new URLSearchParams(new FormData(e.target)).toString();fetch('/',{{method:'POST',body:b,headers:{{'Content-Type':'application/x-www-form-urlencoded'}}}}).then(function(){{nav('/f/apps')}})}}
</script></body></html>"""

def connect_to_wifi():
    def scan():
        networks = ""
        for network in wifi.radio.start_scanning_networks(start_channel=1, stop_channel=14):
            networks += f"<option value='{network.ssid}' data-ch='{network.channel}'>{network.ssid} (ch {network.channel})</option>"
            print(network.ssid, "ch", network.channel)
        wifi.radio.stop_scanning_networks()
        return networks
    networks = scan()
    wifi_error = latest_wifi_error()
    error_html = f'<p class="error-msg">{wifi_error}</p>' if wifi_error else ""
    return f"""<div class="logo">
    <h1>WiFi Setup</h1>
    <p>Connect to a wireless network</p>
</div>
<div class="card">
    <label for="ssid">Network</label>
    <select id="ssid" name="ssid">{networks}</select>
    <script>
    var _ssid = document.getElementById("ssid");
    function _sendSSID(el) {{
        var opt = el.options[el.selectedIndex];
        var v = opt.value.replace(/#/g, "%23");
        var ch = opt.getAttribute("data-ch") || "";
        fetch("/?ssid=" + v + "&channel=" + ch, {{ method: "POST" }});
    }}
    _ssid.addEventListener("change", function() {{ _sendSSID(_ssid); }});
    _ssid.addEventListener("click",  function() {{ _sendSSID(_ssid); }});
    if (_ssid.options.length) _sendSSID(_ssid);
    </script>
    <label for="password">Password</label>
    <input type="text" id="password" name="password" placeholder="Enter password">
    <script>
    document.getElementById("password").addEventListener("blur", function(e) {{
        var p = e.target.value.replace(/#/g, "%23");
        fetch("/?password=" + encodeURIComponent(p), {{ method: "POST" }});
    }});
    </script>
    <button class="btn btn-full" onclick="fetch('/connect').then(function(){{location.reload()}})">Connect</button>
    {error_html}
</div>"""

def _preset_buttons():
    def _pbtn(label, s, w, h, svg, rot=None):
        rot_js = f"var _r=document.getElementById('rotation');if(_r){{_r.value={rot};var _rv=document.getElementById('v_rotation');if(_rv)_rv.textContent={rot};}}" if rot is not None else ""
        return f'<button class="btn btn-sm" onclick="if(confirm(\'Switch to {label} ({w}x{h})? Device will reboot.\')){{var _ew=document.getElementById(\'width\');if(_ew){{_ew.value={w};var _vw=document.getElementById(\'v_width\');if(_vw)_vw.textContent={w};}}var _eh=document.getElementById(\'height\');if(_eh){{_eh.value={h};var _vh=document.getElementById(\'v_height\');if(_vh)_vh.textContent={h};}}{rot_js}fetch(\'/preset?s={s}\',{{method:\'POST\'}})}}" title="{label} {w}x{h}">{svg}<br><span style="font-size:.6rem">{label}</span></button>'
    return ''.join([
        _pbtn('XS','xs',64,32,'<svg width="20" height="16" viewBox="0 0 20 16"><rect x="4" y="4" width="12" height="8" rx="1" fill="black" stroke="currentColor" stroke-width="1.5"/></svg>'),
        _pbtn('X','x',128,32,'<svg width="28" height="16" viewBox="0 0 28 16"><rect x="2" y="4" width="24" height="8" rx="1" fill="black" stroke="currentColor" stroke-width="1.5"/></svg>'),
        _pbtn('XL','xl',192,32,'<svg width="36" height="16" viewBox="0 0 36 16"><rect x="2" y="4" width="32" height="8" rx="1" fill="black" stroke="currentColor" stroke-width="1.5"/></svg>', rot=180),
        _pbtn('2X','2x',128,64,'<svg width="24" height="18" viewBox="0 0 24 18"><rect x="2" y="1" width="20" height="16" rx="1" fill="black" stroke="currentColor" stroke-width="1.5"/></svg>'),
    ])

_showed_wifi = False

def _apps_content():
    global _showed_wifi
    wifi_html = ""
    if not wifi.radio.connected:
        wifi_html = connect_to_wifi()
        _showed_wifi = True
    installed_apps = ""
    for app in os.listdir("/"):
        if app == "LICENSE": continue
        if not "." in app:
            try:
                if not "__init__.py" in os.listdir("/" + app): continue
            except: continue
            ver = _app_ver(app)
            ver_html = f'<div style="font-size:.7rem;color:var(--muted);margin-top:2px">v{ver}</div>' if ver else ''
            installed_apps += f'<div class="app-item"><div><span class="app-name">{app}</span>{ver_html}</div>' + """<button class="btn btn-sm" onclick="run"""+app+"""()">&#9654; Run</button>
<script>function run"""+app+"""() {
    fetch("/?run="""+app+"""", { method: "GET" }).then(() => {
        setTimeout(() => { window.location.href = "/"; }, 10);
    });}</script></div>"""
    if not installed_apps:
        installed_apps = '<p style="color:var(--muted);text-align:center;padding:20px 0;font-size:.9rem">No apps installed yet</p>'
    preset_html = '<div class="card" style="margin-top:10px"><div class="section-title">Screen Size</div><div class="action-row">' + _preset_buttons() + '</div></div>' if _showed_wifi else ''
    return wifi_html + preset_html + """<div class="logo">
    <h1><span style="color:#fff">Matrix</span><span style="color:#f0c800;font-weight:900">BOX</span></h1>
    <p>Select an app to launch</p>
</div>
<div class="card">
    <div class="section-title">Installed Apps</div>
    """ + installed_apps + """
</div>
<button class="btn btn-full btn-success" onclick="nav('/f/download')">&#x2B07; Download Apps</button>
<button class="btn btn-full btn-ghost" onclick="nav('/f/settings')">&#9881; Settings</button>
<div class="card" style="margin-top:10px;border:1px dashed var(--muted)">
    <div class="section-title" style="color:var(--muted)">Built-in Tools</div>
    <div class="app-item"><span class="app-name" style="color:var(--muted)">&#x1F4BB; Terminal</span><button class="btn btn-sm" style="background:var(--muted);color:var(--bg)" onclick="window.location.href='/cmd'">Open</button></div>
    <div class="app-item"><span class="app-name" style="color:var(--muted)">&#x1F4C1; File Manager</span><button class="btn btn-sm" style="background:var(--muted);color:var(--bg)" onclick="window.location.href='/fm'">Open</button></div>
</div>
"""

def select_app():
    return _shell(_apps_content())

@ampule.route('/settingsx')
def _settings(request):
    global settings
    print(__main__.settings)
    return (200, {}, str(settings))

@ampule.route('/connect')
def _connect(request):
    clearscreen()
    print(connect_to_network())
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route('/connectx')
def _connectx(request):
    return (200, {}, select_app() + connect_to_wifi())

@ampule.route('/', method="POST")
def webinterface_post(request):
    global settings
    print("POSTED! ", request.params)
    try:
        pairs = request.body.split('&')
        parsed_data = {}
        for pair in pairs:
            key, value = pair.split('=')
            parsed_data[key] = url_decoder(value)
        request.params = parsed_data
        print(parsed_data)
        print("POSTED body:", request.body)
        for setting in parsed_data:
            if parsed_data[setting] or setting in ("autostart", "screensaver"):
                try:
                    val = parsed_data[setting]
                    if setting not in ("autostart", "screensaver") and setting in settings and type(settings[setting]) is int:
                        val = int(val)
                    settings[setting] = val
                except: pass
        clearscreen(True)
        savesettings(settings)
        clearscreen(False)
        __main__.autostart = settings.get("autostart", False)
        __main__.screensaver_app = settings.get("screensaver", "")
        try: apply_display_settings()
        except Exception as e: print("apply_display_settings:", e)
        return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")
    except: pass

    try: 
        if "unlock" in request.params:
            try: 
                with open("unlock","w") as f: f.write("")
            except: pass
            import safemode
        if "ssid" in request.params:
            __main__.settings["ssid"] = url_decoder(request.params["ssid"])
        if "channel" in request.params:
            try: __main__.settings["channel"] = int(request.params["channel"])
            except: pass
        if "password" in request.params:
            __main__.settings["password"] = url_decoder(request.params["password"])
            #wifi.radio.connect(settings["ssid"], settings["password"])
        if "delete" in request.params:
            dir = request.params["delete"]
            error_color = "green"
            try:
                os.chdir(dir)
                files = os.listdir()
                total = len(files)
                clearscreen(False)
                for x, file in enumerate(files):
                    _draw_progress(x, total, file, label="deleting")
                clearscreen(True)
                for x, file in enumerate(files):
                    try:
                        os.remove(file)
                    except Exception as e:
                        error_color = "red"
                        print(e)
                clearscreen(False)
                _draw_progress(total, total, files[-1] if files else "", error_color == "red", label="deleting")
            finally:
                os.chdir("/")
            try: os.rmdir(dir)
            except: pass
            pprint("done!", color=error_color, line=-1, _refresh=True)
        if "install" in request.params:
            print(request.params["install"])
            install_app(request.params["install"])
    except Exception as e: print(e)
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route('/bootloader', method='POST')
def bootloader(request):
    import microcontroller
    microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)
    microcontroller.reset()
    return (200, {}, "None")

@ampule.route("/preset", method='POST')
def _preset(request):
    presets = {"xs": (64, 32), "x": (128, 32), "xl": (192, 32), "2x": (128, 64)}
    if request.params and "s" in request.params:
        p = request.params["s"]
        if p in presets:
            w, h = presets[p]
            settings["width"] = w
            settings["height"] = h
            settings["tiles"] = 1
            if p == "xl": settings["rotation"] = 180
            savesettings(settings)
            microcontroller.reset()
    return (200, {}, "")

@ampule.route("/rotate", method='POST')
def _rotate(request):
    if request.params and "v" in request.params:
        new_r = int(request.params["v"])
    else:
        new_r = (display.rotation + 90) % 360
    settings["rotation"] = new_r
    display.rotation = new_r
    clearscreen(lines=True)
    try: __main__.show_logo()
    except:
        pprint("Rotated: " + str(new_r), line=0)
        pprint(str(display.width) + "x" + str(display.height))
    return (200, {}, "")

def _settings_content():
    global settings
    rotate_btn = '<button class="btn btn-sm" onclick="fetch(\'/rotate\',{method:\'POST\'}).then(()=>{{var v=document.getElementById(\'v_rotation\');if(v){{var c=parseInt(v.textContent)||0;c=(c+90)%360;v.textContent=c;var s=document.getElementById(\'rotation\');if(s)s.value=c;}}}});">&#128260; 90&deg;</button>'
    preset_btns = _preset_buttons()
    return """<div class="logo"><h1>Settings</h1><p>Configure your device</p></div>
<div class="card"><div class="section-title">Quick Actions</div><div class="action-row action-row-fill">""" + rotate_btn + preset_btns + """</div></div>
<div class="card"><div class="section-title">Device Settings</div>""" + f"""{textbox(settings)}</div>

<div class="card action-row">""" + unlock + """</div>"""

@ampule.route("/settings")
def _settings_route(request):
    return (200, {}, _shell(_settings_content(), "Settings", "/f/settings"))

@ampule.route("/save", method='POST')
def _save(request):
    global settings
    savesettings(settings)
    return (200, {}, '{"ok":true}')

def _download_content():
    free = _fmt_size(_free_space())
    apps = list_available_apps(get_updates())
    return """<div class="logo"><h1>Apps</h1><p>Install or update apps</p></div>
<div class="card" style="text-align:center;padding:12px"><span style="font-size:.8rem;color:var(--muted)">Available space: </span><span style="font-size:.9rem;font-weight:700;color:#fff;text-shadow:0 0 8px rgba(255,255,255,.4)">""" + free + """</span></div>
<div class="card"><div class="section-title">Available</div>""" + str(apps) + """</div>"""

@ampule.route('/download')
def download(request):
    return (200, {}, _shell(_download_content(), "Apps", "/f/download"))

@ampule.route("/f/apps")
def _f_apps(request):
    return (200, {}, _apps_content())

@ampule.route("/f/settings")
def _f_settings(request):
    return (200, {}, _settings_content())

@ampule.route("/f/download")
def _f_download(request):
    return (200, {}, _download_content())

@ampule.route("/f/rssi")
def _f_rssi(request):
    try:
        ai = wifi.radio.ap_info
        rssi = ai.rssi if ai else -100
    except:
        rssi = -100
    return (200, {"Content-Type": "text/plain"}, str(rssi))


####################################################
# DEBUG FUNKTIONER
####################################################

import cmd
import filemanager


@ampule.route('/favicon.svg')
def _favicon(request):
    return (200, {'Content-Type': 'image/svg+xml', 'Cache-Control': 'max-age=86400'}, _FAVICON_SVG)

@ampule.route("/settingsx")
def showsettings(request):
    return (200, {}, str(settings))

@ampule.route('/reset', method='POST')
def reset(request):
    try: os.remove("reboot_required")
    except OSError: pass
    microcontroller.reset()

@ampule.route('/led', method='POST')
def led_toggle(request):
    off = _led_toggle()
    return (200, {}, json.dumps({"off": off}))

# Move /led to system_routes so it survives app route clearing
for _r in ampule.routes:
    if _r[0].match("/led"):
        ampule.system_routes.append(_r)
        ampule.routes.remove(_r)
        break


def url_decoder(url):
    url_decode = {"%C3A4":"�", "%20": " ", "%21": "!", "%22": "\"", "%23": "#", "%24": "$", "%25": "%", "%26": "&", "%27": "'", "%28": "(", "%29": ")", "%2A": "*", "%2B": "+", "%2C": ",", "%2D": "-", "%2E": ".", "%2F": "/", "%30": "0", "%31": "1", "%32": "2", "%33": "3", "%34": "4", "%35": "5", "%36": "6", "%37": "7", "%38": "8", "%39": "9", "%3A": ":", "%3B": ";", "%3C": "<", "%3D": "=", "%3E": ">", "%3F": "?", "%40": "@", "%41": "A", "%42": "B", "%43": "C", "%44": "D", "%45": "E", "%46": "F", "%47": "G", "%48": "H", "%49": "I", "%4A": "J", "%4B": "K", "%4C": "L", "%4D": "M", "%4E": "N", "%4F": "O", "%50": "P", "%51": "Q", "%52": "R", "%53": "S", "%54": "T", "%55": "U", "%56": "V", "%57": "W", "%58": "X", "%59": "Y", "%5A": "Z", "%5B": "[", "%5C": "\\", "%5D": "]", "%5E": "^", "%5F": "_", "%60": "`", "%61": "a", "%62": "b", "%63": "c", "%64": "d", "%65": "e", "%66": "f", "%67": "g", "%68": "h", "%69": "i", "%6A": "j", "%6B": "k", "%6C": "l", "%6D": "m", "%6E": "n", "%6F": "o", "%70": "p", "%71": "q", "%72": "r", "%73": "s", "%74": "t", "%75": "u", "%76": "v", "%77": "w", "%78": "x", "%79": "y", "%7A": "z", "%7B": "{", "%7C": "|", "%7D": "}", "%7E": "~", "%E2%82%AC": "\u20ac", "%E2%80%9A": "\u201a", "%C6%92": "\u0192", "%E2%80%9E": "\u201e", "%E2%80%A6": "\u2026", "%E2%80%A0": "\u2020", "%E2%80%A1": "\u2021", "%CB%86": "\u02c6", "%E2%80%B0": "\u2030", "%C5%A0": "\u0160", "%E2%80%B9": "\u2039", "%C5%92": "\u0152", "%C5%BD": "\u017d", "%E2%80%98": "\u2018", "%E2%80%99": "\u2019", "%E2%80%9C": "\u201c", "%E2%80%9D": "\u201d", "%E2%80%A2": "\u2022", "%E2%80%93": "\u2013", "%E2%80%94": "\u2014", "%CB%9C": "\u02dc", "%E2%84": "\u2122", "%C5%A1": "\u0161", "%E2%80": "\u203a", "%C5%93": "\u0153", "%C5%B8": "\u0178", "%C2%A1": "\u00a1", "%C2%A2": "\u00a2", "%C2%A3": "\u00a3", "%C2%A4": "\u00a4", "%C2%A5": "\u00a5", "%C2%A6": "\u00a6", "%C2%A7": "\u00a7", "%C2%A8": "\u00a8", "%C2%A9": "\u00a9", "%C2%AA": "\u00aa", "%C2%AB": "\u00ab", "%C2%AD": "\u00ac", "%C2%AE": "\u00ae", "%C2%AF": "\u00af", "%C2%B0": "\u00b0", "%C2%B1": "\u00b1", "%C2%B2": "\u00b2", "%C2%B3": "\u00b3", "%C2%B4": "\u00b4", "%C2%B5": "\u00b5", "%C2%B6": "\u00b6", "%C2%B7": "\u00b7", "%C2%B8": "\u00b8", "%C2%B9": "\u00b9", "%C2%BA": "\u00ba", "%C2%BB": "\u00bb", "%C2%BC": "\u00bc", "%C2%BD": "\u00bd", "%C2%BE": "\u00be", "%C2%BF": "\u00bf", "%C3%80": "\u00c0", "%C3%81": "\u00c1", "%C3%82": "\u00c2", "%C3%83": "\u00c3", "%C3%84": "\u00c4", "%C3%85": "\u00c5", "%C3%86": "\u00c6", "%C3%87": "\u00c7", "%C3%88": "\u00c8", "%C3%89": "\u00c9", "%C3%8A": "\u00ca", "%C3%8B": "\u00cb", "%C3%8C": "\u00cc", "%C3%8D": "\u00cd", "%C3%8E": "\u00ce", "%C3%8F": "\u00cf", "%C3%90": "\u00d0", "%C3%91": "\u00d1", "%C3%92": "\u00d2", "%C3%93": "\u00d3", "%C3%94": "\u00d4", "%C3%95": "\u00d5", "%C3%96": "\u00d6", "%C3%97": "\u00d7", "%C3%98": "\u00d8", "%C3%99": "\u00d9", "%C3%9A": "\u00da", "%C3%9B": "\u00db", "%C3%9C": "\u00dc", "%C3%9D": "\u00dd", "%C3%9E": "\u00de", "%C3%9F": "\u00df", "%C3%A0": "\u00e0", "%C3%A1": "\u00e1", "%C3%A2": "\u00e2", "%C3%A3": "\u00e3", "%C3%A4": "\u00e4", "%C3%A5": "\u00e5", "%C3%A6": "\u00e6", "%C3%A7": "\u00e7", "%C3%A8": "\u00e8", "%C3%A9": "\u00e9", "%C3%AA": "\u00ea", "%C3%AB": "\u00eb", "%C3%AC": "\u00ec", "%C3%AD": "\u00ed", "%C3%AE": "\u00ee", "%C3%AF": "\u00ef", "%C3%B0": "\u00f0", "%C3%B1": "\u00f1", "%C3%B2": "\u00f2", "%C3%B3": "\u00f3", "%C3%B4": "\u00f4", "%C3%B5": "\u00f5", "%C3%B6": "\u00f6", "%C3%B7": "\u00f7", "%C3%B8": "\u00f8", "%C3%B9": "\u00f9", "%C3%BA": "\u00fa", "%C3%BB": "\u00fb", "%C3%BC": "\u00fc", "%C3%BD": "\u00fd", "%C3%BE": "\u00fe", "%C3%BF": "\u00ff", 
"%C4%8C":"\u010c",
"%C4%86":"\u0106",
"%C5%BD":"\u017d",
"%C4%90":"\u0110",
"%C5%A0":"\u0160",
"%C4%8D":"\u010d",
"%C4%87":"\u0107",
"%C5%BE":"\u017e",
"%C4%91":"\u0111",
"%C5%A1":"\u0161",
"%E2%82%BF":"?"}

    url = url.replace("+", " ")
    for char in url_decode: url = url.replace(char, url_decode[char])
    return url


####################################################
# REPL
####################################################
import binascii

@ampule.route('/repl', method='POST')
def _repl(request):
    try:
        code = binascii.a2b_base64(request.body).decode()
        _repl_buf = []
        def _repl_print(*args, **kwargs):
            end = kwargs.get("end", "\n")
            sep = kwargs.get("sep", " ")
            _repl_buf.append(sep.join(str(a) for a in args) + end)
        ns = {"print": _repl_print}
        ns.update(globals())
        ns["print"] = _repl_print
        exec(code, ns)
        out = binascii.b2a_base64("".join(_repl_buf).encode()).decode().strip()
        return (200, {}, '{"ok":true,"output":"' + out + '"}')
    except Exception as e:
        out = binascii.b2a_base64(str(e).encode()).decode().strip()
        return (200, {}, '{"ok":false,"output":"' + out + '"}')


####################################################
# AI AGENT PAGE
####################################################

def _ai_content():
    from load_settings import settings as _s
    _sets = _s()
    _aip = _sets.get("ai_provider", "github")
    _aik = _sets.get("ai_key", "")
    _aim = _sets.get("ai_model", "openai/gpt-4o-mini")
    def _sel(v): return ' selected' if _aip == v else ''
    return f"""<div class="logo"><h1>&#x1F916; AI Agent</h1><p>Chat with AI to modify your MatrixBox</p></div>
<div class="card" id="ai-chat">
<div id="ai-log" style="max-height:50vh;overflow-y:auto;margin-bottom:12px;font-size:.88rem"></div>
<textarea id="ai-input" rows="3" placeholder="Ask the AI to read, modify, or create files..."
style="width:100%;background:var(--surface2);border:1.5px solid var(--border);border-radius:var(--r);padding:10px 13px;color:var(--text);font-size:.95rem;font-family:inherit;outline:none;resize:vertical"></textarea>
<div style="display:flex;gap:8px;margin-top:8px">
<button class="btn btn-full" id="ai-send" onclick="_aiSend()">&#x2728; Send</button>
<button class="btn btn-sm btn-ghost" onclick="_aiClear()">Clear</button>
<button class="btn btn-sm btn-ghost" onclick="_aiSync('refresh')" title="Download latest prompt from repo">&#x2B07; Pull</button>
<button class="btn btn-sm btn-ghost" onclick="_aiSync('push')" title="Upload prompt to repo (owner only)">&#x2B06; Push</button>
</div>
</div>
<div class="card" style="margin-top:12px"><div class="section-title">AI Settings</div>
<label>Provider</label>
<select id="ai_prov" onchange="_aip2()">
<option value="github"{_sel('github')}>GitHub Models</option>
<option value="anthropic"{_sel('anthropic')}>Anthropic (Claude)</option>
<option value="openai"{_sel('openai')}>OpenAI</option>
<option value="gemini"{_sel('gemini')}>Google Gemini</option>
<option value="openrouter"{_sel('openrouter')}>OpenRouter</option>
</select>
<label>API Key</label>
<input type="password" id="ai_key" placeholder="Enter API key..." value="{_aik}">
<label>Model</label>
<select id="ai_model"></select>
<button class="btn btn-full" style="margin-top:8px" onclick="_aisave()">Save AI Settings</button>
</div>
<script>
var _aiLog=document.getElementById('ai-log');
var _aiIn=document.getElementById('ai-input');
function _aiMsg(role,text){{
var d=document.createElement('div');
d.style.cssText='padding:8px 10px;margin:4px 0;border-radius:8px;white-space:pre-wrap;word-break:break-word;';
if(role==='user'){{d.style.background='var(--surface3)';d.style.borderLeft='3px solid var(--accent)';}}
else if(role==='error'){{d.style.background='var(--surface2)';d.style.borderLeft='3px solid #ff4444';d.style.color='#ff7070';}}
else if(role==='tool'){{d.style.background='var(--surface)';d.style.borderLeft='3px solid var(--accent2)';d.style.fontSize='.8rem';d.style.color='var(--muted)';}}
else{{d.style.background='var(--surface2)';d.style.borderLeft='3px solid var(--accent2)';}}
d.textContent=text;_aiLog.appendChild(d);_aiLog.scrollTop=_aiLog.scrollHeight;}}
function _aiSend(){{
var msg=_aiIn.value.trim();if(!msg)return;
_aiMsg('user',msg);_aiIn.value='';
var btn=document.getElementById('ai-send');btn.disabled=true;btn.textContent='Thinking...';
fetch('/ai/chat',{{method:'POST',body:msg}}).then(function(r){{return r.json()}}).then(function(d){{
if(d.reply)_aiMsg('assistant',d.reply);
else if(d.error)_aiMsg('error',d.error);
if(d.results&&d.results.length){{
d.results.forEach(function(r){{
var s=r.tool+(r.path?' '+r.path:'')+(r.ok?' OK':' FAILED');
if(r.error)s+=' - '+r.error;
if(r.entries){{s+='\\n';r.entries.forEach(function(e){{if(typeof e==='object')s+=e.name+(e.size!=null?' ('+e.size+'b)':'')+' ';else s+=e+' '}});}}
if(r.total!=null)s+='\\nTotal: '+(r.total/1024).toFixed(1)+'KB, Used: '+(r.used/1024).toFixed(1)+'KB, Free: '+(r.free/1024).toFixed(1)+'KB';
if(r.output)s+='\\n'+r.output;
if(r.content)s+='\\n'+r.content.substring(0,500);
_aiMsg('tool',s);
}});}}
}}).catch(function(e){{_aiMsg('error','Connection error: '+e.message);
}}).finally(function(){{btn.disabled=false;btn.innerHTML='&#x2728; Send';}});
}}
function _aiClear(){{
if(!confirm('Clear conversation history?'))return;
fetch('/ai/clear',{{method:'POST'}}).then(function(){{_aiLog.innerHTML='';_aiMsg('assistant','History cleared. How can I help?');}});
}}
function _aiSync(action){{
var btn=event.target;btn.disabled=true;var t=btn.textContent;btn.textContent='...';
fetch('/ai/'+action+'-prompt',{{method:'POST'}}).then(function(r){{return r.json()}}).then(function(d){{
_aiMsg(d.ok?'assistant':'error',(action==='push'?'Push':'Pull')+': '+d.result);
}}).catch(function(e){{_aiMsg('error',e.message);}}).finally(function(){{btn.disabled=false;btn.textContent=t;}});
}}
var _aim2={{github:[['openai/gpt-4o-mini','GPT-4o Mini'],['openai/gpt-4o','GPT-4o'],['openai/gpt-4.1-nano','GPT-4.1 Nano'],['openai/gpt-4.1-mini','GPT-4.1 Mini'],['meta/Llama-4-Scout-17B-16E-Instruct','Llama 4 Scout']],anthropic:[['claude-sonnet-4-20250514','Claude Sonnet 4'],['claude-haiku-4-20250414','Claude Haiku 4']],openai:[['gpt-4o-mini','GPT-4o Mini'],['gpt-4o','GPT-4o']],gemini:[['gemini-2.0-flash','Gemini 2.0 Flash'],['gemini-2.5-flash','Gemini 2.5 Flash']],openrouter:[['google/gemini-2.0-flash-exp:free','Gemini Flash (Free)'],['meta-llama/llama-4-scout-17b-16e-instruct:free','Llama 4 Scout (Free)']]}};
function _aip2(){{var p=document.getElementById('ai_prov').value,s=document.getElementById('ai_model');s.innerHTML='';_aim2[p].forEach(function(m){{var o=document.createElement('option');o.value=m[0];o.textContent=m[1];s.appendChild(o)}});var cur='{_aim}';s.querySelectorAll('option').forEach(function(o){{if(o.value==cur)o.selected=true}})}}
_aip2();
function _aisave(){{var b='ai_provider='+document.getElementById('ai_prov').value+'&ai_key='+encodeURIComponent(document.getElementById('ai_key').value)+'&ai_model='+encodeURIComponent(document.getElementById('ai_model').value);fetch('/',{{method:'POST',body:b,headers:{{'Content-Type':'application/x-www-form-urlencoded'}}}}).then(function(){{document.getElementById('ai_key').style.borderColor='var(--accent)';setTimeout(function(){{document.getElementById('ai_key').style.borderColor=''}},1500)}})}}
_aiIn.addEventListener('keydown',function(e){{if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();_aiSend();}}}});
fetch('/ai/history').then(function(r){{return r.json()}}).then(function(h){{
if(h.length===0){{_aiMsg('assistant','Hello! I can read, write, and modify any file on your MatrixBox. What would you like to do?');return;}}
h.forEach(function(m){{_aiMsg(m.role,m.content);}});
}});
</script>"""

@ampule.route('/ai')
def _ai_route(request):
    return (200, {}, _shell(_ai_content(), "AI Agent", "/f/ai"))

@ampule.route('/f/ai')
def _f_ai(request):
    return (200, {}, _ai_content())

@ampule.route('/ai/chat', method='POST')
def _ai_chat(request):
    import ai_agent
    import gc
    gc.collect()
    try:
        provider = settings.get("ai_provider", "github")
        key = settings.get("ai_key", "")
        model = settings.get("ai_model", "openai/gpt-4o-mini")
        result = ai_agent.chat(request.body, provider, key, model)
        return (200, {}, json.dumps(result))
    except Exception as e:
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route('/ai/history')
def _ai_history(request):
    try:
        import ai_agent
        return (200, {}, json.dumps(ai_agent._history))
    except:
        return (200, {}, "[]")

@ampule.route('/ai/clear', method='POST')
def _ai_clear(request):
    try:
        import ai_agent
        ai_agent._history.clear()
        import gc; gc.collect()
    except: pass
    return (200, {}, '{"ok":true}')

@ampule.route('/ai/push-prompt', method='POST')
def _ai_push(request):
    try:
        import ai_agent
        r = ai_agent._push_prompt()
        return (200, {}, json.dumps({"ok": True, "result": r}))
    except Exception as e:
        return (200, {}, json.dumps({"ok": False, "result": str(e)}))

@ampule.route('/ai/refresh-prompt', method='POST')
def _ai_refresh(request):
    try:
        import ai_agent
        r = ai_agent._refresh_prompt()
        return (200, {}, json.dumps({"ok": True, "result": r}))
    except Exception as e:
        return (200, {}, json.dumps({"ok": False, "result": str(e)}))


