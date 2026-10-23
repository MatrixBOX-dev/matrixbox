import sys, json, time
import displayio
import bitmaptools
import gc
import wifi

import load_screen
from __main__ import *
microcontroller.cpu.frequency = 240000000
exit = False
padding_length = 20
default_offset = 0
default_scale = 1
scroll_mode = "h"  # "h" horizontal, "v" vertical, "s" static
static_align = "center"  # "left", "center", "right"
btc = 0
currency = "usd"
delay = 30
reverse_direction = 1   # 0 = left-to-right (normal), 1 = right-to-left
shadow_color = 0

shadow_color_map = {
    "black": 0,
    "yellow": 1,
    "brightwhite": 2,
    "blue": 3,
    "red": 4,
    "white": 5,
    "light_blue": 6,
    "green": 7,
    "grey": 8,
    "black2": 9,
    "pink": 10,
    "orange": 11,
}


load_screen.currentfont = font_large

SETTINGS_FILE = "scroller_settings.json"

def get_font_name():
    f = load_screen.currentfont
    if f is font_mini: return "mini"
    if f is font_small: return "small"
    return "large"

def save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"mode": scroll_mode, "align": static_align, "reverse": reverse_direction,
                        "shadow": shadow_color, "font": get_font_name(), "color": load_screen.currentcolor}, f)
    except: pass

def load_settings():
    global scroll_mode, static_align, reverse_direction, shadow_color
    try:
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
        scroll_mode = s.get("mode", "h")
        static_align = s.get("align", "center")
        reverse_direction = s.get("reverse", 1)
        shadow_color = s.get("shadow", 0)
        fm = {"mini": font_mini, "small": font_small, "large": font_large}
        load_screen.currentfont = fm.get(s.get("font", "large"), font_large)
        load_screen.currentcolor = s.get("color", "white")
    except: pass

with open("scroller.html") as f: html_body = f.read()

try:
    with open("scroller.txt") as f:
        scroller_text = f.read()
except:
    scroller_text = "http://" + str(wifi.radio.ipv4_address)

# ---------------------------------------------------------
#  GLOBALS FOR SCROLLER
# ---------------------------------------------------------

big_bitmap = None          # full text bitmap
viewport_bitmap = None     # 128x32 window
viewport_tg = None         # TileGrid for viewport
scroller_width = 0         # width of big_bitmap
scroller_height = 0        # height of big_bitmap (vertical mode)
scroll_x = 0               # current horizontal scroll offset
scroll_y = 0               # current vertical scroll offset

DISPLAY_WIDTH = settings["width"]
DISPLAY_HEIGHT = settings["height"]
PALETTE_SIZE = 10          # matches your existing palette

# ---------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------

def padded(text):
    return " " * padding_length + text + " " * padding_length

def rebuild_scene():
    """Rebuild big bitmap, viewport, and display group based on current text/font/scale."""
    global big_bitmap, viewport_bitmap, viewport_tg
    global scroller_width, scroller_height, scroll_x, scroll_y

    font = load_screen.currentfont
    lines = scroller_text.replace("\r", "").split("\n")

    if scroll_mode == "v":
        # --- Vertical: stack lines in a tall bitmap ---
        line_h = DISPLAY_HEIGHT
        n = len(lines)
        total_h = (n + 2) * line_h
        scroller_height = total_h

        big_bitmap = displayio.Bitmap(DISPLAY_WIDTH, total_h, PALETTE_SIZE)

        for i, ln in enumerate(lines):
            if not ln.strip():
                continue
            tmp = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, PALETTE_SIZE)
            pprint(
                ln, line=0, font=font,
                color=load_screen.currentcolor, _refresh=False,
                window=tmp, block=True, shadow_color=shadow_color,
            )
            y_off = (i + 1) * line_h
            bitmaptools.blit(
                big_bitmap, tmp, 0, y_off,
                x1=0, y1=0, x2=DISPLAY_WIDTH, y2=DISPLAY_HEIGHT,
            )

        gc.collect()
        scroll_y = -DISPLAY_HEIGHT

    elif scroll_mode == "s":
        # --- Static: render text with line breaks ---
        fh = font["fontheight"]
        line_h = fh + 2  # font height + small gap
        n = len(lines)
        total_h = max(DISPLAY_HEIGHT, n * line_h + 2)
        max_w = max((strlen(ln, font) for ln in lines if ln.strip()), default=1)
        if max_w < 1:
            max_w = 1
        scroller_width = max_w

        big_bitmap = displayio.Bitmap(max_w, total_h, PALETTE_SIZE)
        for i, ln in enumerate(lines):
            if not ln.strip():
                continue
            tmp = displayio.Bitmap(max_w, DISPLAY_HEIGHT, PALETTE_SIZE)
            pprint(
                ln, line=0, font=font,
                color=load_screen.currentcolor, _refresh=False,
                window=tmp, block=True, shadow_color=shadow_color,
            )
            y_off = i * line_h
            bitmaptools.blit(
                big_bitmap, tmp, 0, y_off,
                x1=0, y1=0, x2=max_w, y2=min(DISPLAY_HEIGHT, total_h - y_off),
            )

        if scroller_width <= DISPLAY_WIDTH:
            if static_align == "left":
                scroll_x = 0
            elif static_align == "right":
                scroll_x = -(DISPLAY_WIDTH - scroller_width)
            else:
                scroll_x = -(DISPLAY_WIDTH - scroller_width) // 2
        else:
            scroll_x = 0

    else:
        # --- Horizontal: join lines with gap, add padding ---
        gap = " " * padding_length
        text = padded(gap.join(lines))

        scroller_width = strlen(text, font)
        if scroller_width < 1:
            scroller_width = 1

        big_bitmap = displayio.Bitmap(scroller_width, DISPLAY_HEIGHT, PALETTE_SIZE)
        pprint(
            text, line=0, font=font,
            color=load_screen.currentcolor, _refresh=False,
            window=big_bitmap, block=True, shadow_color=shadow_color,
        )
        # Start fully off-screen in the direction text will scroll from, matching
        # the wrap-around reset values used in the main loop below. Previously this
        # was hardcoded to DISPLAY_WIDTH, which put the viewport partway (or past)
        # scroller_width right away -- fine for long text (just skips the lead-in),
        # but for short text it immediately satisfied the "fully scrolled past"
        # blank condition in blit_viewport(), so the display stayed black.
        scroll_x = -scroller_width if reverse_direction else DISPLAY_WIDTH + scroller_width

    # Viewport bitmap (fixed display size)
    viewport_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, PALETTE_SIZE)

    # TileGrid for viewport
    viewport_tg = displayio.TileGrid(
        viewport_bitmap,
        pixel_shader=palette,
        x=0,
        y=default_offset,
    )

    # Group and root
    group = displayio.Group(scale=default_scale)
    group.append(viewport_tg)
    display.root_group = group

def blit_viewport():
    """Copy the visible slice from big_bitmap into viewport_bitmap."""
    if big_bitmap is None or viewport_bitmap is None:
        return

    viewport_bitmap.fill(0)

    if scroll_mode == "v":
        src_y0 = max(scroll_y, 0)
        src_y1 = min(scroll_y + DISPLAY_HEIGHT, scroller_height)
        h = src_y1 - src_y0
        if h <= 0:
            return
        dst_y = max(0, -scroll_y)
        w = min(DISPLAY_WIDTH, big_bitmap.width)
        bitmaptools.blit(
            viewport_bitmap, big_bitmap,
            0, dst_y,
            x1=0, y1=src_y0, x2=w, y2=src_y0 + h,
        )
    else:
        src_x0 = max(scroll_x, 0)
        src_x1 = min(scroll_x + DISPLAY_WIDTH, scroller_width)
        w = src_x1 - src_x0
        if w <= 0:
            return
        dst_x = max(0, -scroll_x)
        bitmaptools.blit(
            viewport_bitmap, big_bitmap,
            dst_x, 0,
            x1=src_x0, y1=0, x2=src_x0 + w, y2=DISPLAY_HEIGHT,
        )

# ---------------------------------------------------------
#  WEB ROUTES
# ---------------------------------------------------------

@ampule.route("/exit", method="GET")
def web_exit(request):
    global exit
    exit = True
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/save", method="POST")
def web_save(request):
    with open("scroller.txt", "w") as f:
        f.write(scroller_text)
    return (200, {}, "OK")

@ampule.route("/", method="POST")
def scroller_post(request):
    global scroller_text, exit, default_offset, default_scale, shadow_color
    global btc, scroll_mode, padding_length, scroll_x, scroll_y, reverse_direction, static_align

    if "btc" in request.params:
        btc = 1 - btc

    if "mode" in request.params:
        m = request.params["mode"]
        if m in ("h", "v", "s"):
            scroll_mode = m
            rebuild_scene()
        save_settings()
        return (200, {}, "OK")

    if "scroll" in request.params:
        if scroll_mode == "s":
            scroll_mode = "h"
        else:
            scroll_mode = "s"
        rebuild_scene()
        save_settings()
        return (200, {}, "OK")

    if "text" in request.params:
        scroller_text = ampule.url_decoder(request.params["text"]).replace("\\n", "\n").replace("\r", "")
    if "reverse" in request.params:
        try:
            reverse_direction = int(request.params["reverse"])
        except:
            reverse_direction = 1 - reverse_direction
        save_settings()
        return (200, {}, "OK")

    if "size" in request.params:
        size = request.params["size"]
        if size == "mini":
            load_screen.currentfont = font_mini
        if size == "small":
            load_screen.currentfont = font_small
        if size == "large":
            load_screen.currentfont = font_large

    if "color" in request.params:
        load_screen.currentcolor = request.params["color"]

    if "rgb" in request.params:
        try:
            raw = request.params["rgb"].replace("%23", "").replace("#", "")
            r = int(raw[0:2], 16)
            g = int(raw[2:4], 16)
            b = int(raw[4:6], 16)
            palette[5] = (r, g, b)
            load_screen.currentcolor = "white"
        except:
            pass

    if "align" in request.params:
        a = request.params["align"]
        if a in ("left", "center", "right"):
            static_align = a
            if scroll_mode == "s":
                rebuild_scene()
            save_settings()
            return (200, {}, "OK")

    if "offset" in request.params:
        default_offset = int(request.params["offset"])

    if "scale" in request.params:
        default_scale = int(request.params["scale"])

    if "shadow_color" in request.params:
        name = request.params["shadow_color"]
        if name in shadow_color_map:
            shadow_color = shadow_color_map[name]
        rebuild_scene()
        save_settings()
        return (200, {}, "OK")

    if btc:
        set_btc()
    else:
        rebuild_scene()

    save_settings()
    return (200, {}, "OK")

@ampule.route("/", method="GET")
def scroller_get(request):
    return (200, {}, header("Scroller", app=True) + html_body + footer())

# ---------------------------------------------------------
#  BTC TEXT
# ---------------------------------------------------------

def set_btc():
    global scroller_text
    try:
        data = requests.get(
            "https://min-api.cryptocompare.com/data/generateAvg?fsym=BTC&tsym=USD&e=coinbase"
        ).text
        data = json.loads(data)
        scroller_text = "₿ $" + data["DISPLAY"]["PRICE"].replace("$ ", "").split(".")[0]
    except Exception as e:
        scroller_text = str(e)

    rebuild_scene()

# ---------------------------------------------------------
#  INITIALIZE
# ---------------------------------------------------------

clearscreen()
load_settings()
rebuild_scene()

# ---------------------------------------------------------
#  MAIN LOOP
# ---------------------------------------------------------

while not exit:
    ampule.listen(socket)

    if scroll_mode == "h":
        if reverse_direction == 0:
            scroll_x -= 1
            if scroll_x <= -scroller_width: scroll_x = DISPLAY_WIDTH + scroller_width
        else:
            scroll_x += 1
            if scroll_x >= DISPLAY_WIDTH + scroller_width: scroll_x = -scroller_width
    elif scroll_mode == "v":
        if reverse_direction == 1:
            scroll_y += 1
            if scroll_y >= scroller_height: scroll_y = -DISPLAY_HEIGHT
        else:
            scroll_y -= 1
            if scroll_y <= -DISPLAY_HEIGHT: scroll_y = scroller_height

    blit_viewport()
    refresh()

    b = check_if_button_pressed()
    if b == 1:
        if scroll_mode == "h":
            scroll_mode = "v"
        elif scroll_mode == "v":
            scroll_mode = "s"
        else:
            scroll_mode = "h"
        rebuild_scene()
    if b == 2:
        sys.exit()

clearscreen()

