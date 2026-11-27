import sys, json, time
import displayio
import bitmaptools
import gc
import wifi
import storage

import load_screen
from __main__ import *

# `from __main__ import *` above only copies whatever display/palette/etc.
# objects existed in __main__'s namespace at this exact moment -- a one-time
# snapshot, not a live reference. displaytext/__init__.py just rebuilt all of
# these (init_display(bit_depth=5)) before importing this file, so fetching
# them directly from load_screen guarantees this file draws into the
# Bitmap/Palette that are actually on screen right now, not a stale,
# orphaned pre-rebuild one (see the same bug/fix in flights/code.py).
display = load_screen.display
window = load_screen.window
palette = load_screen.palette
matrix = load_screen.matrix
rf_group = load_screen.rf_group
tile_groupgroup = load_screen.tile_groupgroup

microcontroller.cpu.frequency = 240000000
exit = False
padding_length = 20
default_offset = 0
default_scale = 1
scroll_mode = "h"  # "h" horizontal, "v" vertical, "s" static, "t" typewriter (multi-color, live-edited)
static_align = "center"  # "left", "center", "right"
btc = 0
currency = "usd"
GAP_PX = 24     # blank pixels between repeats of the text (font-independent)
_SHADOW_PAD = 2 # extra pixels per line so a drop shadow is never clipped
reverse_direction = 1   # 0 = left-to-right (normal), 1 = right-to-left
shadow_color = 0
custom_rgb = None  # (r, g, b) when a custom text color was picked via the color picker; None = never set
custom_shadow_rgb = None  # (r, g, b) when a custom shadow color was picked; None = never set
_SHADOW_RGB_INDEX = 13  # dedicated palette slot for the custom shadow color -- unused elsewhere in this app

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

# Writing to a file that already ships with the app (not a new file created
# at runtime) is deliberate, not cosmetic: on
# this device, creating a brand-new file reliably fails with "stream
# operation not supported" -- confirmed by testing both a direct write to a
# new ".json" file and a new ".tmp" file for an atomic rename,
# both of which hit the exact same error a plain overwrite of this
# pre-existing file does not. So there's no working way to create a new
# file here at all, which also rules out the usual temp-file-then-rename
# safety net below (the temp file would itself be a new file). A write that
# fails or is interrupted partway through can still corrupt this file, same
# as before, but it's the only option that can actually persist anything on
# this particular filesystem.
SETTINGS_FILE = "displaytext.txt"

def get_font_name():
    f = load_screen.currentfont
    if f is font_mini: return "mini"
    if f is font_small: return "small"
    return "large"

def save_settings():
    try:
        # json.dump(obj, f) streams the serialization into f via repeated
        # internal .write() calls as it walks the object -- on this device
        # that's exactly what raises "stream operation not supported",
        # regardless of filename. json.dumps(obj) + a single f.write() call
        # is the pattern already proven to work here (same as this app's
        # old plain-text scroller.txt save, and main.py's own
        # savesettings()), so build the full string first and write it once.
        with open(SETTINGS_FILE, "w") as f:
            f.write(json.dumps({"mode": scroll_mode, "align": static_align, "reverse": reverse_direction,
                        "shadow": shadow_color, "font": get_font_name(), "color": load_screen.currentcolor,
                        "offset": default_offset, "scale": default_scale, "custom_rgb": custom_rgb,
                        "custom_shadow_rgb": custom_shadow_rgb, "text": scroller_text, "tw": tw_lines}))
    except Exception as e:
        print("displaytext: save_settings() failed:", e)
        try:
            print("displaytext: filesystem readonly =", storage.getmount("/").readonly)
        except Exception:
            pass

def load_settings():
    global scroll_mode, static_align, reverse_direction, shadow_color, default_offset, default_scale
    global custom_rgb, custom_shadow_rgb, scroller_text, tw_lines
    try:
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
        scroll_mode = s.get("mode", "h")
        static_align = s.get("align", "center")
        reverse_direction = s.get("reverse", 1)
        shadow_color = s.get("shadow", 0)
        default_offset = s.get("offset", default_offset)
        default_scale = s.get("scale", default_scale)
        scroller_text = s.get("text", scroller_text)
        tw_lines = s.get("tw", tw_lines)
        fm = {"mini": font_mini, "small": font_small, "large": font_large}
        load_screen.currentfont = fm.get(s.get("font", "large"), font_large)
        load_screen.currentcolor = s.get("color", "white")
        rgb = s.get("custom_rgb")
        if rgb:
            custom_rgb = tuple(rgb)  # JSON gives a list back, not a tuple
            palette[5] = custom_rgb
        shadow_rgb = s.get("custom_shadow_rgb")
        if shadow_rgb:
            custom_shadow_rgb = tuple(shadow_rgb)
            palette[_SHADOW_RGB_INDEX] = custom_shadow_rgb
            shadow_color = _SHADOW_RGB_INDEX
    except Exception as e:
        print("displaytext: load_settings() failed (using defaults):", e)

with open("displaytext.html") as f: html_body = f.read()

scroller_text = "http://" + str(wifi.radio.ipv4_address)  # overridden by load_settings() below if saved
tw_lines = []  # typewriter mode: list of lines, each a list of {"t": text, "c": "#rrggbb" | "white" (= Text color)} segments
_say_count = 0  # sentences dictated so far; parity picks the alternating color

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
view_w = DISPLAY_WIDTH        # visible content width in horizontal mode (DISPLAY_WIDTH // scale)
DISPLAY_HEIGHT = settings["height"]
PALETTE_SIZE = 10          # matches your existing palette
_TW_VALUES = 20            # typewriter bitmaps address the whole 20-slot palette (_TW_SLOTS goes up to 19)

# ---------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------

def padded(text):
    return " " * padding_length + text + " " * padding_length

_TW_PITCH = {"mini": 6, "small": 8, "large": 16}  # line height per font in typewriter mode
_TW_SPACE = 6  # fixed space width in typewriter mode (the fonts' own space glyphs are only 1-3px)

# At bit_depth=5 any channel below ~11 rounds down to 0, so a dark but non-black
# pick would vanish. Non-zero channels are raised to this floor instead.
_MIN_CHANNEL = 11

def _parse_rgb(raw):
    """'#rrggbb' / 'rrggbb' / '%23rrggbb' -> (r, g, b) with dark channels lifted to the visible floor."""
    raw = raw.replace("%23", "").replace("#", "")
    return tuple(c if c == 0 else max(c, _MIN_CHANNEL) for c in (int(raw[i:i + 2], 16) for i in (0, 2, 4)))

# Palette slots free for typewriter's per-segment colors: 12 is an unused duplicate,
# 13 is the custom shadow, and 14-19 are never used by anything else here.
_TW_SLOTS = (12, 14, 15, 16, 17, 18, 19)

def _tw_color_index(name, slots):
    """Palette index for a segment color: '#rrggbb' gets a slot from _TW_SLOTS
    (shared per render), 'white'/missing is the Text color, other names are legacy named colors."""
    if not name or name == "white":
        return 5
    if name[0] != "#":
        return load_screen._color_map.get(name, 5)
    try:
        rgb = _parse_rgb(name)
    except Exception:
        return 5
    if rgb in slots:
        return slots[rgb]
    if len(slots) < len(_TW_SLOTS):
        slot = _TW_SLOTS[len(slots)]
        palette[slot] = rgb
        slots[rgb] = slot
        return slot
    # Out of slots: reuse the closest color already assigned this render.
    return min(slots.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[0], rgb)))[1]

def _tw_draw_seg(bmp, x, y, text, font, cidx):
    """Draw one single-color text segment at (x, y); returns the x after it."""
    if font is font_mini:
        text = text.lower()
    for ch in text:
        if ch == " ":
            x += _TW_SPACE
            continue
        g = font.get(ch) or font.get("?")
        if g is None:
            x += 4
            continue
        gw = g[0]
        for row in range(len(g) - 1):
            py = y + row
            if not 0 <= py < bmp.height:
                continue
            bits = g[row + 1]
            if not isinstance(bits, int):
                continue
            for col in range(gw):
                px = x + col
                if 0 <= px < bmp.width and (bits >> (gw - 1 - col)) & 1:
                    bmp[px, py] = cidx
        x += gw
    return x

def _tw_render(bmp, font):
    pitch = _TW_PITCH[get_font_name()]
    slots = {}
    for i, segs in enumerate(tw_lines[:DISPLAY_HEIGHT // pitch]):
        y = i * pitch + 1
        if shadow_color:
            x = 2
            for seg in segs:
                x = _tw_draw_seg(bmp, x, y + 1, seg.get("t", ""), font, shadow_color)
        x = 1
        for seg in segs:
            x = _tw_draw_seg(bmp, x, y, seg.get("t", ""), font, _tw_color_index(seg.get("c"), slots))

def _tw_text_width(text, font):
    if font is font_mini:
        text = text.lower()
    w = 0
    for ch in text:
        if ch == " ":
            w += _TW_SPACE
            continue
        g = font.get(ch) or font.get("?")
        w += g[0] if g else 4
    return w

def _tw_wrap(text, font, max_w):
    lines = []
    cur = ""
    for word in text.split():
        test = cur + " " + word if cur else word
        if _tw_text_width(test, font) <= max_w:
            cur = test
            continue
        if cur:
            lines.append(cur)
        cur = word
        while len(cur) > 1 and _tw_text_width(cur, font) > max_w:  # a single word wider than the screen
            n = len(cur) - 1
            while n > 1 and _tw_text_width(cur[:n], font) > max_w:
                n -= 1
            lines.append(cur[:n])
            cur = cur[n:]
    if cur:
        lines.append(cur)
    return lines

def add_dictation(text):
    """Append a spoken sentence to the typewriter text: word-wrapped to the screen,
    alternating between the Text color and a dimmer shade per sentence, and
    scrolled up once the screen is full."""
    global tw_lines, _say_count
    text = text.strip()
    if not text:
        return
    if text[-1] not in ".!?":
        text += "."
    if _say_count % 2 == 0:
        color = "white"
    else:
        color = "#%02x%02x%02x" % tuple(c // 2 for c in (custom_rgb or (20, 20, 20)))
    _say_count += 1
    rows = DISPLAY_HEIGHT // _TW_PITCH[get_font_name()]
    for ln in _tw_wrap(text, load_screen.currentfont, DISPLAY_WIDTH - 2):
        tw_lines.append([{"t": ln, "c": color}])
    tw_lines = tw_lines[-rows:]

def tw_info(with_text=False):
    name = get_font_name()
    pitch = _TW_PITCH[name]
    cols = DISPLAY_WIDTH // (4 if name == "mini" else 6 if name == "small" else 8)
    info = {"w": DISPLAY_WIDTH, "h": DISPLAY_HEIGHT, "rows": DISPLAY_HEIGHT // pitch,
            "cols": cols, "font": name, "mode": scroll_mode, "align": static_align,
            "reverse": reverse_direction}
    if with_text:
        info["tw"] = tw_lines
    return json.dumps(info)

def rebuild_scene():
    """Rebuild big bitmap, viewport, and display group based on current text/font/scale."""
    global big_bitmap, viewport_bitmap, viewport_tg
    global scroller_width, scroller_height, scroll_x, scroll_y, view_w

    font = load_screen.currentfont
    # Horizontal shows DISPLAY_WIDTH // scale content pixels (the group is scaled up);
    # other modes keep their existing behaviour.
    view_w = max(1, DISPLAY_WIDTH // default_scale) if scroll_mode == "h" else DISPLAY_WIDTH
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

    elif scroll_mode == "t":
        # --- Typewriter: per-segment colors, drawn straight onto a screen-sized bitmap ---
        scroller_width = DISPLAY_WIDTH
        big_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, _TW_VALUES)
        _tw_render(big_bitmap, font)
        scroll_x = 0

    else:
        # --- Horizontal: each line rendered separately, GAP_PX pixels apart ---
        parts = [ln for ln in lines if ln.strip()] or [" "]
        widths = [strlen(p, font) + _SHADOW_PAD for p in parts]
        scroller_width = GAP_PX * 2 + sum(widths) + GAP_PX * (len(parts) - 1)
        big_bitmap = displayio.Bitmap(scroller_width, DISPLAY_HEIGHT, PALETTE_SIZE)
        x = GAP_PX
        for p, w in zip(parts, widths):
            seg = displayio.Bitmap(w, DISPLAY_HEIGHT, PALETTE_SIZE)
            pprint(
                p, line=0, font=font,
                color=load_screen.currentcolor, _refresh=False,
                window=seg, block=True, shadow_color=shadow_color,
            )
            bitmaptools.blit(big_bitmap, seg, x, 0)
            x += w + GAP_PX
        # Start fully off-screen on the side the text enters from.
        scroll_x = -view_w if reverse_direction else scroller_width

    # Viewport (fixed display size); bitmaptools.blit needs both bitmaps to have
    # the same depth, so it follows the mode's source bitmap.
    viewport_bitmap = displayio.Bitmap(view_w, DISPLAY_HEIGHT, _TW_VALUES if scroll_mode == "t" else PALETTE_SIZE)

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
        src_x1 = min(scroll_x + view_w, scroller_width)
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
    return (302, {"Location": "/"}, "")

@ampule.route("/save", method="POST")
def web_save(request):
    try:
        save_settings()
    except Exception as e:
        return (500, {}, "ERROR: " + str(e))
    return (200, {}, "OK")

@ampule.route("/info", method="GET")
def web_info(request):
    return (200, {}, tw_info(True))

@ampule.route("/tw", method="POST")
def web_typewriter(request):
    # Body is the JSON line/segment list from the page's live editor. It's
    # re-rendered on every call but only written to flash when the page
    # signals the typing pause with ?save=1.
    global tw_lines, _say_count
    try:
        tw_lines = json.loads(request.body)
        if not tw_lines:
            _say_count = 0  # cleared: dictation starts over with the Text color
        if scroll_mode == "t":
            rebuild_scene()
        if "save" in request.params:
            save_settings()
    except Exception as e:
        print("displaytext: typewriter post failed:", e)
    return (200, {}, tw_info())

@ampule.route("/say", method="POST")
def web_say(request):
    # A sentence of recognized speech (?t=, url-encoded) from the page's Dictate button.
    # Returns the full text so the page's editor shows what is on the display.
    try:
        add_dictation(ampule.url_decoder(request.params.get("t", "")))
        if scroll_mode == "t":
            rebuild_scene()
        save_settings()
    except Exception as e:
        print("displaytext: dictation failed:", e)
    return (200, {}, tw_info(True))

@ampule.route("/", method="POST")
def scroller_post(request):
    global scroller_text, exit, default_offset, default_scale, shadow_color
    global btc, scroll_mode, padding_length, scroll_x, scroll_y, reverse_direction, static_align
    global custom_rgb, custom_shadow_rgb

    if "btc" in request.params:
        btc = 1 - btc

    if "mode" in request.params:
        m = request.params["mode"]
        if m in ("h", "v", "s", "t"):
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
            custom_rgb = _parse_rgb(request.params["rgb"])
            palette[5] = custom_rgb
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

    if "shadow_rgb" in request.params:
        try:
            custom_shadow_rgb = _parse_rgb(request.params["shadow_rgb"])
            palette[_SHADOW_RGB_INDEX] = custom_shadow_rgb
            shadow_color = _SHADOW_RGB_INDEX
        except:
            pass
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
    text_hex = "#%02x%02x%02x" % custom_rgb if custom_rgb else "#ffffff"
    shadow_hex = "#%02x%02x%02x" % custom_shadow_rgb if custom_shadow_rgb else "#000000"
    page = html_body.replace("__CURRENT_COLOR__", text_hex).replace("__CURRENT_SHADOW__", shadow_hex)
    return (200, {}, header("Display Text", app=True) + page + footer())

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
#  SPLASH
# ---------------------------------------------------------

SPLASH_TEXT = "Displaytext"
SPLASH_SCALE = 1
_SPLASH_GREY = 14          # dedicated palette slot for the splash's grey shadow (free until typewriter claims it later)

def splash():
    """Startup splash: SPLASH_TEXT in orange with a grey drop shadow scrolls once,
    right to left, across the screen at SPLASH_SCALE x. Any button press skips it."""
    font = font_large
    text_w = strlen(SPLASH_TEXT, font) + 1  # +1 for the shadow's offset
    palette[_SPLASH_GREY] = (25, 25, 25)

    # Everything below is in pre-scale units: the group's scale multiplies them.
    view_w = DISPLAY_WIDTH // SPLASH_SCALE
    view_h = DISPLAY_HEIGHT // SPLASH_SCALE
    bmp = displayio.Bitmap(text_w, view_h, 16)
    pprint(
        SPLASH_TEXT, line=0, font=font, color="orange", _refresh=False,
        window=bmp, block=True, shadow_color=_SPLASH_GREY,
        top_offset=max(0, (view_h - font["fontheight"]) // 2 - 1),
    )
    tg = displayio.TileGrid(bmp, pixel_shader=palette, x=view_w, y=0)
    group = displayio.Group(scale=SPLASH_SCALE)
    group.append(tg)
    display.root_group = group

    for x in range(view_w, -text_w - 1, -1):
        tg.x = x
        display.refresh()
        if check_if_button_pressed():
            break

# ---------------------------------------------------------
#  INITIALIZE
# ---------------------------------------------------------

clearscreen()
splash()
load_settings()
rebuild_scene()

# ---------------------------------------------------------
#  MAIN LOOP
# ---------------------------------------------------------

while not exit:
    ampule.listen(socket)

    if scroll_mode == "h":
        # One pixel per frame: the loop's CPU speed sets the scroll speed.
        # Text's left edge is at screen x = -scroll_x. Wrap only when the text is
        # completely off-screen, so the re-entry always comes from the edge.
        span = view_w + scroller_width
        if reverse_direction == 0:      # left-to-right
            scroll_x -= 1
            if scroll_x <= -view_w: scroll_x += span
        else:                           # right-to-left
            scroll_x += 1
            if scroll_x >= scroller_width: scroll_x -= span
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
        elif scroll_mode == "s":
            scroll_mode = "t"
        else:
            scroll_mode = "h"
        rebuild_scene()
    if b == 2:
        sys.exit()

clearscreen()

