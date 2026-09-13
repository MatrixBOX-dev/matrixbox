from __main__ import *
from load_screen import *
import sys, board, binascii, json, gc
import bitmaptools
import gifio
import time
from check_button import check_if_button_pressed

exit = False
brightness = 0.25  # 0.0-1.0
selected_gif = None
black_bmp = None
dim_bmp = None
clock_window = displayio.TileGrid(window, pixel_shader=palette)
splash = displayio.Group(scale=1)
splash.append(clock_window)
display.root_group = splash
clearscreen()
if "images" not in os.listdir():
    try: os.mkdir("images")
    except: pass


def list_gifs():
    names = []
    for name in os.listdir("images"):
        if name.startswith("."):
            continue
        if not name.lower().endswith(".gif"):
            continue
        names.append(name)
    return sorted(names)

def safe_gif_name(name):
    name = url_decoder(name or "").replace("\\", "/").split("/")[-1].strip()
    name = name.lstrip(".")
    if not name:
        name = "uploaded.gif"
    if not name.lower().endswith(".gif"):
        name += ".gif"

    return name

def save_base64_gif(data, path):
    # Decode in small, 4-char-aligned slices and write incrementally so we
    # never hold the full decoded image (on top of the already-buffered
    # base64 request body) in RAM at once.
    chunk_chars = 4096
    with open(path, "wb") as f:
        for start in range(0, len(data), chunk_chars):
            chunk = data[start:start + chunk_chars].encode("ascii")
            f.write(binascii.a2b_base64(chunk))
            gc.collect()

files = list_gifs()
print(files)
_index = 0

try:
    with open("gif.html") as f: html_body = f.read()
except: html_body = ""

settings_error = None

def save_settings():
    global settings_error
    try:
        with open("gif_settings.json", "w") as f:
            f.write(json.dumps({"brightness": brightness, "selected_gif": selected_gif}))
        settings_error = None
    except Exception as e:
        print("Could not save gif settings:", e)
        settings_error = "Settings not saved: " + str(e)

def load_settings():
    global brightness, selected_gif
    try:
        with open("gif_settings.json") as f:
            s = json.loads(f.read())
        brightness = s.get("brightness", 0.25)
        selected_gif = s.get("selected_gif")
    except: pass

load_settings()

if selected_gif and selected_gif in files:
    _index = files.index(selected_gif)

@ampule.route("/exit", method="GET")
def webinterface(request):
    global exit
    exit = True
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/", method="GET")
def gif_webinterface(request):
    return (200, {}, header("GIF Player", app=True) + html_body + footer())

@ampule.route("/state", method="GET")
def webinterface_state(request):
    return (200, {}, json.dumps({"brightness": brightness}))

@ampule.route("/gifs", method="GET")
def webinterface_list_gifs(request):
    items = []
    for name in list_gifs():
        try:
            size = os.stat("images/" + name)[6]
        except Exception:
            size = 0
        items.append({"n": name, "s": size})

    return (200, {}, json.dumps(items))

@ampule.route("/gifs/delete", method="POST")
def webinterface_delete_gif(request):
    name = safe_gif_name(request.params.get("name", ""))
    try:
        os.remove("images/" + name)
        return (200, {}, json.dumps({"ok": True}))
    except Exception as e:
        return (200, {}, json.dumps({"ok": False, "error": str(e)}))

@ampule.route("/gifs/select", method="POST")
def webinterface_select_gif(request):
    global _index, odg, files
    name = safe_gif_name(request.params.get("name", ""))
    try:
        odg = load_img("images/" + name)
        files = list_gifs()
        if name in files:
            _index = files.index(name)
        resp = {"ok": True}
        if settings_error:
            resp["warning"] = settings_error
        return (200, {}, json.dumps(resp))
    except Exception as e:
        return (200, {}, json.dumps({"ok": False, "error": str(e)}))

@ampule.route('/', method="POST")
def webinterface_post(request):
    global _index, brightness, odg
    print("POST:ed")
    print(_index)
    print(request.params)

    if "next" in request.params:
        try:
            _index += 1
            odg = load_img()
        except Exception as e:
            print("next failed:", e)
        resp = {"ok": True}
        if settings_error:
            resp["warning"] = settings_error
        return (200, {}, json.dumps(resp))

    if "brightness" in request.params:
        try:
            brightness = float(request.params["brightness"])
            if brightness < 0.0: brightness = 0.0
            if brightness > 1.0: brightness = 1.0
        except: pass
        save_settings()
        resp = {"ok": True}
        if settings_error:
            resp["warning"] = settings_error
        return (200, {}, json.dumps(resp))

    if "sendbase64" in request.params:
        name = safe_gif_name(request.params.get("name", ""))
        path = "images/" + name
        try:
            save_base64_gif(request.body, path)
            odg = load_img(path)
            resp = {"ok": True}
            if settings_error:
                resp["warning"] = settings_error
            return (200, {}, json.dumps(resp))
        except Exception as e:
            print("Upload failed:", e)
            return (500, {}, "Upload failed: " + str(e))

    return (200, {}, """<meta http-equiv="refresh" content="0; url=./" />""")


def apply_brightness(dim_bmp, src_bmp, black_bmp, brightness):
    # bitmaptools.blit() reading from an on-disk-backed bitmap source (as
    # gifio.OnDiskGif.bitmap is) hard-crashes the board with no Python
    # exception raised (see adafruit/circuitpython#5916), so always go
    # through alphablend -- factor_1=1.0 gives the same full-weight copy
    # without that crash.
    bitmaptools.alphablend(
        dim_bmp, src_bmp, black_bmp,
        displayio.Colorspace.RGB565_SWAPPED,
        factor_1=brightness,
    )

def load_img(file=False):
    global black_bmp, dim_bmp, files, selected_gif
    if file:
        pass
    else:
        files = list_gifs()
        if not files:
            raise RuntimeError("No GIFs in images/")
        file = "images/" + files[_index % len(files)]

    name = file.split("/")[-1]
    if name != selected_gif:
        selected_gif = name
        save_settings()

    odg = gifio.OnDiskGif(file)
    w = odg.bitmap.width
    h = odg.bitmap.height
    black_bmp = displayio.Bitmap(w, h, 65536)
    dim_bmp = displayio.Bitmap(w, h, 65536)
    start = time.monotonic()
    next_delay = odg.next_frame() # Load the first frame
    end = time.monotonic()
    overhead = end - start
    # Copy first frame into writable dim_bmp
    try:
        apply_brightness(dim_bmp, odg.bitmap, black_bmp, brightness)
    except Exception as e:
        print("apply_brightness error:", e)
    # Remove old face TileGrids (keep clock_window at index 0)
    while len(splash) > 1:
        splash.pop()
    face = displayio.TileGrid(
        dim_bmp,
        pixel_shader=displayio.ColorConverter(
            input_colorspace=displayio.Colorspace.RGB565_SWAPPED,
            dither=True
        ),
    )
    splash.append(face)
    return odg

if not list_gifs(): pprint("Upload image", _refresh=True)
else: odg = load_img()
time.sleep(0.5)

while not exit:
    ampule.listen(socket)
    time.sleep(0.01)
    try:
        odg.next_frame()
    except Exception as e:
        print("next_frame error:", e)
    try:
        apply_brightness(dim_bmp, odg.bitmap, black_bmp, brightness)
    except Exception as e:
        print("apply_brightness error:", e)
    refresh()

    b = check_if_button_pressed()
    #print(b)
    if b == 1:
        _index += 1
        try: odg = load_img()
        except Exception as e: print("load_img failed:", e)
        time.sleep(0.2)
    elif b == 2: sys.exit()
