from __main__ import * # antingen denna rad eller #settings = load_settings etc
import displayio, board, framebufferio, microcontroller, load_settings, os
from rgbmatrix import RGBMatrix
from microcontroller import watchdog
from font_mini import font_mini
from font_small import font_small
from font_large import font_large

#settings =  load_settings.settings() # behövs för boot.py
displayio.release_displays()



#from watchdog import WatchDogMode
#watchdog.timeout = 60
#watchdog.mode = WatchDogMode.RESET
#def wd(): return watchdog.feed()
if os.uname().machine == "Waveshare ESP32-S3-Zero with ESP32S3": 
    _bit_depth = 4
    addr_pins_placeholder = [board.IO7, board.IO8, board.IO9, board.IO10]
    rgb_pins_placeholder = [board.IO1,board.IO3,board.IO2, board.IO4,board.IO6,board.IO5]
    if settings["height"] == 64: 
        addr_pins_placeholder.append(board.IO17)
        rgb_pins_placeholder = [board.IO1,board.IO2,board.IO3, board.IO4,board.IO5,board.IO6]
    matrix = RGBMatrix(width=settings["width"], height=settings["height"], bit_depth=_bit_depth,
                    rgb_pins=rgb_pins_placeholder,
                    addr_pins = addr_pins_placeholder,
                    clock_pin=board.IO11, latch_pin=board.IO12, output_enable_pin=board.IO13, tile=settings["tiles"],
                    serpentine=False, doublebuffer=True)
elif "N8R8" in os.uname().machine: 
    _bit_depth = 4
    addr_pins_placeholder = [board.GPIO3, board.GPIO8, board.GPIO18, board.GPIO17]
    if settings["height"] == 64: addr_pins_placeholder.append(board.GPIO21)
    matrix = RGBMatrix(width=settings["width"], height=settings["height"], bit_depth=_bit_depth,
                    rgb_pins=[board.GPIO1,board.GPIO2,board.GPIO42, board.GPIO41,board.GPIO40,board.GPIO39],
                    addr_pins = addr_pins_placeholder,
                    clock_pin=board.GPIO12, latch_pin=board.GPIO13, output_enable_pin=board.GPIO14, tile=settings["tiles"],
                    serpentine=False, doublebuffer=True)
elif "ESP32-S2" in os.uname().machine:  # FK-8F1
    _bit_depth = 4
    addr_pins_placeholder = [board.IO38, board.IO37, board.IO36, board.IO35]
    if settings["height"] == 64: addr_pins_placeholder.append(board.IO34)
    matrix = RGBMatrix(width=settings["width"], height=settings["height"], bit_depth=_bit_depth,
                    rgb_pins=[board.IO12, board.IO13, board.IO17, board.IO21, board.IO20, board.IO16],
                    addr_pins=addr_pins_placeholder,
                    clock_pin=board.IO10, latch_pin=board.IO33, output_enable_pin=board.IO11, tile=settings["tiles"],
                    serpentine=False, doublebuffer=True)
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

def _pprint(string, line=False, color="white", font=font_mini, _refresh=False, clear=True, top_offset=0, window=None, _clearscreen=True, hr="(", slow=False, block=False, shadow_color=0):
    """Original pprint with debug output — use for diagnostics."""
    if window is None: window = _current_window()
    print(string)
    global line_window
    print(line_window)
    if _clearscreen:
        string = string + hr * (settings["width"] - strlen(string))
    max_lines = int(5*(settings["height"]*1/32))
    if "int" in str(type(line)):
        _lines = [string]
        line_window = ["" * (int(line) + 1)]
    else:
        line_window.append(string)
        if len(line_window) > max_lines: line_window.pop(0)
        _lines = line_window
    pixwidth = 0
    _color = color if isinstance(color, int) else _color_map.get(color, 5)
    offs = 1 + top_offset
    try:
        for lin, stringline in enumerate(_lines):
            if line: lin = line
            if line == -1: lin = max_lines - 1
            print(lin, len(_lines))
            for character in str(stringline):
                if font == font_mini: character = character.lower()
                if character not in font: character = "_"
                for width in range(font[character][0]):
                    for height in range(font["fontheight"]):
                        invertedwidth = font[character][0] - width
                        if isinstance(font[character][1], int):
                            bit = ((font[character][height+1] >> invertedwidth) & 1)
                            if int(bit):
                                window[width + pixwidth, ((6 * lin) + height) + offs] = _color
                                if block:
                                    sx = width + pixwidth + 1
                                    sy = ((6 * lin) + height) + offs + 1
                                    if 0 <= sx < window.width and 0 <= sy < window.height:
                                        window[sx, sy] = shadow_color
                            else:
                                if not block:
                                    if clear: window[width+pixwidth, ((6*lin) + height)+offs] = 0
                        else: window[width+pixwidth, (height)+offs] = int(font[character][height+1][width])
                if slow: refresh()
                if isinstance(font[character][1], int): pixwidth += font[character][0]
                else: pixwidth += len(font[character][1])
            pixwidth = 0
            if _refresh: refresh()
        if lin + 1 == len(_lines): refresh()
    except Exception as e:
        print(e)

def pprint(string, line=False, color="white", font=font_mini, _refresh=True, clear=True, top_offset=0, window=None, _clearscreen=True, hr="(", slow=False, block=False, shadow_color=0, overlay=False):
    if window is None: window = _current_window()
    _is_mini = (font == font_mini)
    global line_window
    _c = color if isinstance(color, int) else _color_map.get(color, 5)
    fh = font["fontheight"]
    max_lines = int(5 * (display.height * 1 / 32))
    offs = 1 + top_offset

    # Pad string with hr chars when hr is a visible fill character
    if _clearscreen and hr != "(":
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
        if _clearscreen and hr == "(":
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
    _font = font_mini
    fh = _font["fontheight"]
    max_lines = int(5 * (display.height // 32))
    lin = max_lines - 1 if line_num == -1 else line_num
    y_base = (6 * lin) + 1
    w = display.width
    _c = color if isinstance(color, int) else _color_map.get(color, 5)
    new_lower = new_text.lower()
    step = max(2, w // 16)
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
    total = w
    frame = 0
    while frame < total:
        s = min(step, total - frame)
        frame += s
        for y in range(y_base, y_base + fh):
            hi = y - y_base
            for x in range(w - s):
                window[x, y] = window[x + s, y]
            for x in range(w - s, w):
                ci = x - (w - frame)
                window[x, y] = cols[ci][hi] if 0 <= ci < len(cols) else 0
        display.refresh()
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

    new_r = int(settings["rotation"])
    if display.rotation != new_r:
        display.rotation = new_r

    needs_reboot = (matrix.width != int(settings["width"]) or
                    matrix.height != int(settings["height"]))
    if needs_reboot:
        microcontroller.reset()
