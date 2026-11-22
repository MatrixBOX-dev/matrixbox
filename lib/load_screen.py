from __main__ import * # antingen denna rad eller #settings = load_settings etc
import displayio, board, framebufferio, microcontroller, load_settings, os, sys, time
from rgbmatrix import RGBMatrix
from microcontroller import watchdog
from font_mini import font_mini
from font_small import font_small
from font_large import font_large

#settings =  load_settings.settings() # behövs för boot.py
_cc = str(settings.get("color_correct","")).lower() not in ("","false","0")
_sw = lambda p: [p[0],p[2],p[1],p[3],p[5],p[4]] if _cc else p
_bit_depth = 4  # current color bit depth; pass bit_depth=N to init_display() to change it



#from watchdog import WatchDogMode
#watchdog.timeout = 60
#watchdog.mode = WatchDogMode.RESET
#def wd(): return watchdog.feed()

def _build_matrix(bit_depth):
    try: RGBMatrix.deinit(matrix)
    except: print("First instance")
    # Builds a fresh RGBMatrix wired per the current board + settings (width/
    # height/tiles/color_correct/bit_depth). Called from init_display(), both
    # at import time and again at runtime whenever those change.
    machine = os.uname().machine
    if machine == "Waveshare ESP32-S3-Zero with ESP32S3":
        addr_pins_placeholder = [board.IO7, board.IO8, board.IO9, board.IO10]
        rgb_pins_placeholder = [board.IO1,board.IO3,board.IO2, board.IO4,board.IO6,board.IO5]
        if settings["height"] == 64 or settings["height"] == 128: 
            addr_pins_placeholder.append(board.IO17)
            rgb_pins_placeholder = [board.IO1,board.IO2,board.IO3, board.IO4,board.IO5,board.IO6]
        return RGBMatrix(width=settings["width"], height=settings["height"], bit_depth=bit_depth,
                        rgb_pins=_sw(rgb_pins_placeholder),
                        addr_pins = addr_pins_placeholder,
                        clock_pin=board.IO11, latch_pin=board.IO12, output_enable_pin=board.IO13, tile=settings["tiles"],
                        serpentine=False, doublebuffer=True)
    elif "N8R8" in machine: 
        addr_pins_placeholder = [board.GPIO3, board.GPIO8, board.GPIO18, board.GPIO17]
        if settings["height"] == 64: addr_pins_placeholder.append(board.GPIO21)
        return RGBMatrix(width=settings["width"], height=settings["height"], bit_depth=bit_depth,
                        rgb_pins=_sw([board.GPIO1,board.GPIO2,board.GPIO42, board.GPIO41,board.GPIO40,board.GPIO39]),
                        addr_pins = addr_pins_placeholder,
                        clock_pin=board.GPIO12, latch_pin=board.GPIO13, output_enable_pin=board.GPIO14, tile=settings["tiles"],
                        serpentine=False, doublebuffer=True)
    elif "S2" in machine:  # Träskylt
        xpin = (board.IO9)
        if "21" in os.listdir(): xpin = (board.IO21)
        a1pin = (board.IO7)
        a2pin = (board.IO8)
        a3pin = xpin
        a4pin = (board.IO10)
        if "806599e1c20" in os.listdir():
            a1pin = (board.IO37)
            a2pin = (board.IO38)
            a3pin = (board.IO39)
            a4pin = (board.IO40)
        _rgb_pins = [board.IO1,board.IO2,board.IO3,board.IO4,board.IO5,board.IO6] if not "reverse" in os.listdir() else [board.IO1,board.IO3,board.IO2, board.IO4,board.IO6,board.IO5]
        return RGBMatrix(
                        width=settings["width"], height=settings["height"], bit_depth=bit_depth,
                        rgb_pins=_rgb_pins,
                        addr_pins=[a1pin, a2pin, a3pin, a4pin],
                        clock_pin=board.IO11, latch_pin=board.IO12, output_enable_pin=board.IO13, tile=1,
                        serpentine=False, doublebuffer=True)

def _geometry():
    # The subset of settings that are baked into the RGBMatrix at construction
    # time -- changing any of these means the matrix/display must be rebuilt,
    # unlike rotation which framebufferio can change on the existing display.
    # _bit_depth isn't a persisted setting (apps pass it to init_display()
    # directly), but it's just as fixed at construction time, so it has to be
    # tracked here too -- otherwise apply_display_settings() would see no
    # settings change and skip rebuilding, leaving an app's bit depth
    # override in place after e.g. a rotation change.
    color_correct = str(settings.get("color_correct","")).lower() not in ("","false","0")
    return (int(settings["width"]), int(settings["height"]), int(settings["tiles"]), color_correct, _bit_depth)

_last_geometry = None

def _sync_dependent_modules():
    # main.py, web_interface.py, filemanager.py, patches.py, cmd.py etc. all
    # grab matrix/display/window/palette/rf_group/tile_groupgroup by name
    # (`from __main__ import *` / `from load_screen import *`), which only
    # copies whatever object existed at import time. After rebuilding them
    # below, push the fresh objects into every already-imported module still
    # holding one of those names so nothing is left pointing at the released
    # display.
    live = {"matrix": matrix, "display": display, "window": window,
            "palette": palette, "rf_group": rf_group, "tile_groupgroup": tile_groupgroup}
    for mod in sys.modules.values():
        d = getattr(mod, "__dict__", None)
        if not d: continue
        for name, value in live.items():
            if name in d: d[name] = value

def init_display(bit_depth=None):
    """(Re)builds the RGB matrix, display and drawing surfaces from the
    current settings -- the exact same mechanism Settings' width/height/
    tiles/color_correct controls use (via apply_display_settings()), just
    callable directly. Called once at import time, and safe to call again at
    runtime.

    `bit_depth` defaults to whatever is already set; pass an explicit value
    (e.g. init_display(bit_depth=6)) for an app that needs deeper color at
    the cost of max refresh rate -- main.py's initialize_app() calls
    init_display(bit_depth=4) on every app exit as a safety net. A no-op if
    the requested bit_depth already matches and nothing else
    (width/height/tiles/color_correct) changed either."""
    global matrix, display, window, palette, rf_group, tile_groupgroup, line_window, _overlays, _cc, _last_geometry, _bit_depth
    if bit_depth is not None: _bit_depth = bit_depth
    _cc = str(settings.get("color_correct","")).lower() not in ("","false","0")
    if _last_geometry is not None and _geometry() == _last_geometry:
        return
    try:
        displayio.release_displays()  # frees the previous matrix's pins/framebuffer, if any

        matrix = _build_matrix(_bit_depth)

        try: microcontroller.cpu.frequency = 180000000
        except: pass
        print("--------------------------------------------------------- ")
        print(" CHIP:           ", os.uname().machine)
        print(" FREQUENCY:      ", microcontroller.cpu.frequency)
        print("--------------------------------------------------------- ")

        display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False, rotation=settings["rotation"])
        rf_group = displayio.Group()
        display.root_group = rf_group
        display.refresh()
        display.root_group.hidden = True
        rows = int((settings["height"]*1/32))
        print(rows)
        _max_dim = max(settings["width"], settings["height"] * rows)
        window = displayio.Bitmap(_max_dim, _max_dim, 16) # viewport large enough for any rotation
        line_window = [] # en lista för multi-line printout till skärmen
        _overlays = []
        palette = displayio.Palette(20, dither=False)

        tile_group = displayio.TileGrid(window, pixel_shader=palette)
        rf_group = displayio.Group()
        tile_groupgroup = displayio.Group()
        tile_groupgroup.append(tile_group)
        rf_group.append(tile_groupgroup)
        display.root_group = rf_group

        palette[0] = (0)    # vit
        palette[1] = (50,50,00)    # vit
        palette[2] = (100,100,100)    # bright white
        palette[3] = (0, 59, 122)      # morkbla
        palette[4] = (100,0,0)     # rod
        palette[5] = (20,20,20)    # grey
        palette[6] = (20,20,40)    #  ?
        palette[7] = (0, 100, 10)      # green
        palette[8] = (0, 0, 100)    # pink
        palette[9] = (0, 30, 3)    # dark green
        palette[11] = (50,30,0)    # orange
        palette[12] = (0,0,100)    # orange

        # doublebuffer=True needs a frame actually pushed into BOTH internal
        # buffers before the physical LEDs reliably show new content -- the
        # single refresh() above (right after the first, near-empty
        # `rf_group`) only primes one of them.
        display.refresh()

        _last_geometry = _geometry()
        _sync_dependent_modules()
    except Exception as e:
        # Hot reinit is best-effort -- if the matrix/display can't be rebuilt
        # cleanly (e.g. a board quirk releasing pins), fall back to the old
        # behavior rather than leaving the screen half-initialized.
        print("init_display failed, falling back to full reset:", e)
        microcontroller.reset()

init_display()


currentfont = font_mini 
currentcolor = "white"
_overlays = []  # list of (string, lin, _c, font, _is_mini, fh, offs, block, shadow_color)

def display_width():
    return display.width

def display_height():
    return display.height

def strlen(_string, font_size=font_mini): 
    if font_size==font_mini: _string = _string.lower()
    return sum(font_size[c][0] for c in _string if c in font_size) # mäter längden på hel string

def _current_window():
    return window

_color_map = {"black":0,"yellow":1,"brightwhite":2,"bright_white":2,"bright-white":2,"blue":3,"red":4,"white":5,"light_blue":6,"green":7,"grey":8,"black2":9,"pink":10,"orange":11}

def pprint(string, line=False, color="white", font=font_mini, _refresh=True, clear=True, top_offset=0, window=None, _clearscreen=True, hr=None, slow=False, block=False, shadow_color=0, overlay=False):
    if window is None: window = _current_window()
    _is_mini = (font == font_mini)
    global line_window
    _c = color if isinstance(color, int) else _color_map.get(color, 5)
    fh = font["fontheight"]
    max_lines = int(5 * (display.height * 1 / 32))
    offs = 1 + top_offset

    # Pad string with hr chars when hr is a visible fill character
    if _clearscreen and hr is not None:
        pad_char = hr.lower() if _is_mini else hr
        if pad_char in font:
            cw = font[pad_char][0]
            remaining = settings["width"] - strlen(string, font)
            if remaining > 0 and cw > 0:
                string = string + hr * (remaining // cw)

    if overlay:
        # Pure overlay: only write lit pixels, touch nothing else
        lin = line if ("int" in str(type(line)) and line) else 0
        if "int" in str(type(line)) and line == -1: lin = max_lines - 1
        _overlays.append((string, lin, _c, font, _is_mini, fh, offs, block, shadow_color))
        _draw_line(window, string, lin, _c, font, _is_mini, fh, offs, False, block, shadow_color)
        if slow or _refresh: refresh()
        return

    if "int" in str(type(line)):
        lin = line if line else 0
        if line == -1: lin = max_lines - 1
        while len(line_window) <= lin:
            line_window.append("")
        line_window[lin] = string
        _draw_line(window, string, lin, _c, font, _is_mini, fh, offs, clear, block, shadow_color)
        if _clearscreen and hr is None:
            _clear_row_remainder(window, strlen(string, font), lin, fh, offs)
    else:
        line_window.append(string)
        if len(line_window) > max_lines: line_window.pop(0)
        for lin, stringline in enumerate(line_window):
            _draw_line(window, stringline, lin, _c, font, _is_mini, fh, offs, clear, block, shadow_color)
            if _clearscreen:
                _clear_row_remainder(window, strlen(stringline, font), lin, fh, offs)

    cleared_lines = set()
    for ov in _overlays:
        if ov[1] not in cleared_lines:
            _clear_row_remainder(window, 0, ov[1], ov[5], ov[6])
            cleared_lines.add(ov[1])
    for ov in _overlays:
        _draw_line(window, ov[0], ov[1], ov[2], ov[3], ov[4], ov[5], ov[6], False, ov[7], ov[8])

    if slow or _refresh: refresh()

def _draw_line(win, string, lin, _c, font, _is_mini, fh, offs, clear, block, shadow_color):
    px = 0
    y_base = (6 * lin) + offs
    max_x = win.width
    chars = []
    for ch in str(string):
        if _is_mini: ch = ch.lower()
        if ch not in font: ch = "_"
        glyph = font[ch]
        gw = glyph[0]
        if px + gw > max_x:
            break
        chars.append((ch, glyph, gw, px))
        px += gw
    # shadow pass
    if block:
        for ch, glyph, gw, px_off in chars:
            is_bitmap = isinstance(glyph[1], int)
            if is_bitmap:
                for w in range(gw):
                    inv_w = gw - w
                    for h in range(fh):
                        bit = (glyph[h + 1] >> inv_w) & 1
                        if bit:
                            sx = w + px_off + 1
                            sy = y_base + h + 1
                            if 0 <= sx < win.width and 0 <= sy < win.height:
                                win[sx, sy] = shadow_color
    # foreground pass
    for ch, glyph, gw, px_off in chars:
        is_bitmap = isinstance(glyph[1], int)
        if is_bitmap:
            for w in range(gw):
                inv_w = gw - w
                for h in range(fh):
                    y = y_base + h
                    bit = (glyph[h + 1] >> inv_w) & 1
                    if bit:
                        win[w + px_off, y] = _c
                    elif clear and not block:
                        win[w + px_off, y] = 0
        else:
            for w in range(gw):
                for h in range(fh):
                    win[w + px_off, h + offs] = int(glyph[h + 1][w])

def _clear_row_remainder(win, text_px_width, lin, fh, offs):
    y_base = (6 * lin) + offs
    x_start = text_px_width
    x_end = min(win.width, settings["width"])
    for x in range(x_start, x_end):
        for h in range(fh):
            win[x, y_base + h] = 0

"""def clearscreen():
    global line_window
    window.fill(0)
    line_window = []
    refresh()"""

def scroll_line(new_text, line_num=-1, color="yellow"):
    """Replace a text row with an eight-frame vertical-blinds reveal."""
    _font = font_mini
    fh = _font["fontheight"]
    max_lines = int(5 * (display.height // 32))
    lin = max_lines - 1 if line_num == -1 else line_num
    y_base = (6 * lin) + 1
    w = display.width
    _c = color if isinstance(color, int) else _color_map.get(color, 5)
    new_lower = new_text.lower()
    cols = []
    for ch in new_lower:
        if ch not in _font: ch = "_"
        g = _font[ch]
        gw = g[0]
        for wx in range(gw):
            inv_w = gw - wx
            col = []
            for h in range(fh):
                col.append(_c if (g[h + 1] >> inv_w) & 1 else 0)
            cols.append(col)
    for frame in range(8):
        for x in range(frame, w, 8):
            for hi in range(fh):
                window[x, y_base + hi] = cols[x][hi] if x < len(cols) else 0
        display.refresh()
        time.sleep(0.02)
    global line_window
    while len(line_window) <= lin:
        line_window.append("")
    line_window[lin] = new_text

def refresh(): display.refresh()

def clearscreen(on_or_off=False, lines=False):
    global line_window, _overlays
    display.root_group.hidden = on_or_off
    if lines: 
        window.fill(0)
        line_window = []
        _overlays = []
    refresh()

def pset(x,y,c):
    window[x,y] = c

def apply_display_settings():
    try: wifi.radio.tx_power = float(settings["wifi_power"])
    except: pass

    if _geometry() != _last_geometry:
        # width/height/tiles/color_correct are fixed at RGBMatrix construction
        # time, so the matrix+display have to be torn down and rebuilt.
        # init_display() also picks up the current rotation, so there's
        # nothing left to do below in that case.
        init_display()
    else:
        new_r = int(settings["rotation"])
        if display.rotation != new_r:
            display.rotation = new_r
