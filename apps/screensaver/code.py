from __main__ import *
import sys

EFFECTS = []

for directory in os.listdir():
    if "." not in directory:
        EFFECTS.append(directory)

EFFECTS.sort()

# Load saved choice
try:
    with open("sv_settings.json") as f:
        _sv_cfg = json.loads(f.read())
except:
    _sv_cfg = {"effect": "starcloud"}

def _save_sv():
    try:
        with open("sv_settings.json", "w") as f:
            f.write(json.dumps(_sv_cfg))
    except:
        pass  # Read-only filesystem — effect change still works in memory

# Global switch flag (True = switch effect, False = exit app)
_sv_switch = False

_SELECT_STYLE = ("width:100%;background:var(--surface2);border:1.5px solid var(--border);"
                 "border-radius:var(--r);padding:10px 12px;color:var(--text);"
                 "font-size:.93rem;outline:none;-webkit-appearance:none")

# Web UI
@ampule.route("/", method="GET")
def sv_index(request):
    try:
        effect = _sv_cfg.get("effect", "starcloud")
        opts = ""
        for e in EFFECTS:
            sel = " selected" if e == effect else ""
            opts += "<option value='" + e + "'" + sel + ">" + e[0].upper() + e[1:] + "</option>"
        dropdown = ("<div class='card'><div class='section-title'>Effect</div>"
                    "<select style='" + _SELECT_STYLE + "' onchange='svSwitch(this.value)'>"
                    + opts + "</select></div>")
        mod = sys.modules.get(effect)
        fragment = getattr(mod, "SETTINGS_FRAGMENT", "") if mod else ""
        script = ("<script>function svSwitch(v){fetch('/?effect='+v,{method:'POST'})"
                  ".then(function(){setTimeout(function(){location.reload()},1500)})}</script>")
        return (200, {}, header("Screensaver", app=True) + dropdown + fragment + script + footer())
    except Exception as e:
        return (200, {}, "ERR: " + str(e))

@ampule.route("/", method="POST")
def sv_post(request):
    global _sv_switch
    if request.params and "effect" in request.params:
        e = request.params["effect"]
        if e in EFFECTS:
            _sv_cfg["effect"] = e
            _save_sv()
            _sv_switch = True
            load_settings.app_running = False
    return (200, {}, "{}")

@ampule.route("/exit", method="GET")
def sv_exit(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

# Manager routes only; effects append their own and we reset to this before each
# import so a previous effect's stale routes can't shadow the live handlers.
_base_routes = ampule.routes[:]

# Run the selected effect; loop to support live switching
while True:
    _sv_switch = False
    load_settings.app_running = True

    effect = _sv_cfg.get("effect", "starcloud")
    if effect not in EFFECTS:
        effect = "starcloud"

    # Remove cached modules so re-import re-runs their code
    for _m in EFFECTS:
        if _m in sys.modules:
            del sys.modules[_m]

    ampule.routes[:] = _base_routes  # drop the previous effect's routes

    if effect == "aquarium":
        import aquarium
    elif effect == "fireworks":
        import fireworks
    elif effect == "rain":
        import rain
    elif effect == "space":
        import space
    else:
        import starcloud

    if not _sv_switch:
        break  # Normal exit (button press or /exit)
