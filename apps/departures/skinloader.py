"""Download-on-demand loader for pluggable /departures rendering skins.

Built-in skins ("scroll", "list") are rendered directly by functions.py's
scroll_mode()/list_mode() and never touch this module. Anything else is a
"plugin" skin: its source lives in the separate departures_skins repo and is
fetched into skins/<id>/ the first time it's selected, then exec'd into its
own namespace (rather than a normal import) so same-named files
(renderer.py) from different skins never collide in sys.modules.
"""
from __main__ import requests
import os, json

_REPO_RAW = "https://raw.githubusercontent.com/MatrixBOX-dev/departures_skins/main/"
_SKINS_DIR = "skins"

# Registry of skins downloadable from the skins repo. Label is shown in the
# web UI even before the skin has ever been downloaded.
PLUGIN_SKINS = {
    "tfl_dlr": {"label": "TfL DLR (London)"},
}

_cache = {}  # skin_id -> exec'd namespace, kept warm while the app is running

def _dir(skin_id):
    return _SKINS_DIR + "/" + skin_id

def is_downloaded(skin_id):
    try:
        return "renderer.py" in os.listdir(_dir(skin_id))
    except:
        return False

def download(skin_id):
    """Fetch a plugin skin's manifest + files from the skins repo."""
    d = _dir(skin_id)
    try: os.mkdir(_SKINS_DIR)
    except: pass
    try: os.mkdir(d)
    except: pass
    r = requests.get(_REPO_RAW + skin_id + "/manifest.json", timeout=10)
    manifest = json.loads(r.text)
    r.close()
    for fname in manifest.get("files", ["renderer.py"]):
        r = requests.get(_REPO_RAW + skin_id + "/" + fname, timeout=10)
        if r.status_code != 200:
            r.close()
            raise Exception("skin download failed: " + fname + " (" + str(r.status_code) + ")")
        text = r.text
        r.close()
        with open(d + "/" + fname, "w") as f:
            f.write(text)
    with open(d + "/manifest.json", "w") as f:
        f.write(json.dumps(manifest))

def load(skin_id):
    """Return the skin's exec'd namespace, downloading it first if needed."""
    if skin_id in _cache:
        return _cache[skin_id]
    if not is_downloaded(skin_id):
        download(skin_id)
    path = _dir(skin_id) + "/renderer.py"
    with open(path) as f:
        src = f.read()
    ns = {"__name__": "skin_" + skin_id}
    exec(compile(src, path, "exec"), ns)
    _cache[skin_id] = ns
    return ns
