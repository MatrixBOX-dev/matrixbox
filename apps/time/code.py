from __main__ import *
import sys, time, gc, math
import displayio, bitmaptools
import load_screen
from check_button import check_if_button_pressed
from load_screen import *

# Invisible 1px-wide glyph for pixel-precise padding. Falls back to "("
# (also blank, same width) while the OS-side font update from #25 is still
# rolling out.
BLANK = "\x00" if "\x00" in font_mini and "\x00" in font_small and "\x00" in font_large else "("

with open("time.html") as f: html_body = f.read()

DISP_W = settings["width"]
DISP_H = settings["height"]

SETTINGS_FILE = "timesettings.txt"
try:
    with open(SETTINGS_FILE) as f:
        cfg = json.loads(f.read())
except:
    cfg = {}

# "function" (clock / stopwatch / countdown) selects WHAT value is shown;
# "mode" (digital / analog / analog_rect) selects HOW it's drawn -- the two
# are independent, so e.g. a countdown can be shown as an analog dial with
# hands tracking the remaining time. Colors/dial/typography settings are
# shared across all three functions; only the clock-specific info row
# (weekday/date/temperature) and the countdown-specific preset are
# function-specific.
_DEFAULTS = {"function": "clock", "mode": "digital",
    "show_date": 1, "show_day": 1, "show_seconds": 0, "show_temp": 0, "city": "",
    "f_hex": "#ffffff", "b_hex": "#000000", "scale": 1, "font": "large",
    "hour_hex": "#ffffff", "min_hex": "#4488ff", "sec_hex": "#ff4444",
    "show_border": 1, "h12": 0, "blink_colon": 1, "rainbow": 0,
    "accent": 0, "accent_hex": "#4488ff", "show_dots": 1, "dots_hex": "#ffffff",
    "shadow_hex": "", "frame_hex": "", "show_shadow": 1,
    "preset_ms": 60000, "show_tenths": 1}
for _k, _v in _DEFAULTS.items():
    if _k not in cfg: cfg[_k] = _v

def save_cfg():
    try:
        # A single f.write(json.dumps(...)) call, NOT json.dump(obj, f) --
        # the latter streams the serialization into f via many small
        # internal .write() calls, which on at least one device in this
        # fleet reliably fails with "stream operation not supported" no
        # matter the filename. A single write of the whole string is the
        # pattern proven to work (see the /scroller app's save_settings()).
        with open(SETTINGS_FILE, "w") as f:
            f.write(json.dumps(cfg))
    except Exception as e:
        print("time: save_cfg() failed:", e)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def apply_colors():
    fg = hex_to_rgb(cfg["f_hex"])
    bg = hex_to_rgb(cfg["b_hex"])
    palette[0] = (0, 0, 0)
    palette[5] = fg
    palette[11] = (20, 20, 20)  # countdown progress-bar track -- fixed, not user-configurable
    if cfg.get("show_shadow", 1):
        palette[12] = hex_to_rgb(cfg["shadow_hex"]) if cfg.get("shadow_hex") else (fg[0] // 4, fg[1] // 4, fg[2] // 4)
    else:
        palette[12] = (0, 0, 0)
    palette[13] = hex_to_rgb(cfg["frame_hex"]) if cfg.get("frame_hex") else (fg[0] // 6, fg[1] // 6, fg[2] // 6)
    palette[14] = bg
    palette[15] = hex_to_rgb(cfg["hour_hex"])
    palette[16] = hex_to_rgb(cfg["min_hex"])
    palette[17] = hex_to_rgb(cfg["sec_hex"])
    palette[18] = hex_to_rgb(cfg["dots_hex"])
    palette[19] = hex_to_rgb(cfg["accent_hex"])

def _hsv_to_rgb(h):
    h = h % 360
    s = 6
    i = h // 60
    f = h - i * 60
    q = (60 - f) * 255 // 60
    t = f * 255 // 60
    if i == 0: return (255 // s, t // s, 0)
    if i == 1: return (q // s, 255 // s, 0)
    if i == 2: return (0, 255 // s, t // s)
    if i == 3: return (0, q // s, 255 // s)
    if i == 4: return (t // s, 0, 255 // s)
    return (255 // s, 0, q // s)

def selectfont(selectedfont):
    if selectedfont == "mini": load_screen.currentfont = font_mini
    elif selectedfont == "small": load_screen.currentfont = font_small
    else: load_screen.currentfont = font_large
    cfg["font"] = selectedfont
    return load_screen.currentfont

def _render_dim_text(text, x, y):
    """Render text in font_mini at palette 18 (dim) onto screen."""
    tw = strlen(text, font_mini)
    tmp = displayio.Bitmap(tw + 1, 6, 20)
    pprint(text, 0, font=font_mini, clear=False, color="white",
           top_offset=-1, _refresh=False, window=tmp, _clearscreen=False)
    for py in range(tmp.height):
        for px in range(tmp.width):
            if tmp[px, py] == 5:
                tmp[px, py] = 18
    bitmaptools.blit(screen, tmp, x, y,
                     x1=0, y1=0, x2=tmp.width, y2=tmp.height,
                     skip_source_index=0)

load_screen.currentfont = selectfont(cfg["font"])

# ── Stopwatch / countdown state machine (from the old /stopwatch app) ───────
SW_STOPPED  = 0
SW_RUNNING  = 1
SW_PAUSED   = 2
SW_FINISHED = 3
_STATE_NAMES  = ["stopped", "running", "paused", "finished"]
_STATE_LABELS = ["Ready", "Running", "Paused", "Done"]

sw_state      = SW_STOPPED
sw_elapsed_ms = 0
sw_start_mono = 0.0

def _now_ms():
    if sw_state == SW_RUNNING:
        return int((time.monotonic() - sw_start_mono) * 1000) + sw_elapsed_ms
    return sw_elapsed_ms

def _start():
    global sw_state, sw_start_mono, sw_elapsed_ms
    if cfg["function"] == "countdown" and sw_elapsed_ms >= int(cfg["preset_ms"]):
        sw_elapsed_ms = 0
    sw_state      = SW_RUNNING
    sw_start_mono = time.monotonic()

def _pause():
    global sw_state, sw_elapsed_ms
    if sw_state == SW_RUNNING:
        sw_elapsed_ms = _now_ms()
        sw_state = SW_PAUSED

def _reset():
    global sw_state, sw_elapsed_ms, sw_start_mono, _last_tstr, _last_analog
    sw_state      = SW_STOPPED
    sw_elapsed_ms = 0
    sw_start_mono = 0.0
    _last_tstr    = ""
    _last_analog  = ""

def _toggle():
    if   sw_state == SW_RUNNING:  _pause()
    elif sw_state == SW_FINISHED: _reset()
    else:                         _start()

# ── Web server ───────────────────────────────────────────────────────────────
@ampule.route("/exit", method="GET")
def exit_webinterface(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

@ampule.route("/", method="GET")
def webinterface(request):
    return (200, {}, header("Time", app=True) + html_body + footer())

@ampule.route("/settings", method="GET")
def get_settings(request):
    return (200, {}, json.dumps(cfg))

@ampule.route("/state", method="GET")
def get_state(request):
    ms   = _now_ms()
    disp = max(0, int(cfg["preset_ms"]) - ms) if cfg["function"] == "countdown" else ms
    return (200, {}, json.dumps({
        "state":     _STATE_NAMES[sw_state],
        "ms":        disp,
        "function":  cfg["function"],
        "preset_ms": int(cfg["preset_ms"])
    }))

# POST param handlers: (param_name, action)
#   "int"  -> store as int
#   "hex"  -> store as "#" + value
_INT_PARAMS = ["show_date", "show_day", "show_seconds", "h12", "blink_colon", "accent", "show_shadow", "show_tenths"]
_HEX_PARAMS = ["f_hex", "b_hex", "hour_hex", "min_hex", "sec_hex", "accent_hex", "dots_hex", "shadow_hex", "frame_hex"]
_ANALOG_RESET = ["show_border", "show_dots"]

@ampule.route("/", method="POST")
def time_webinterface_post(request):
    global cfg, delay, temp_string, _last_analog
    p = request.params
    if "save" in p:
        display.root_group.hidden = True; refresh()
        save_cfg()
        display.root_group.hidden = False
        delay = 0

    if "action" in p:
        a = p["action"]
        if   a == "start":  _start()
        elif a == "pause":  _pause()
        elif a == "toggle": _toggle()
        elif a == "reset":  _reset()

    if "function" in p and p["function"] in ("clock", "stopwatch", "countdown"):
        cfg["function"] = p["function"]
        _reset()
        delay = 0

    if "preset" in p:
        try:
            raw = p["preset"].replace("%3A", ":").replace("+", " ").strip()
            if ":" in raw:
                pts = raw.split(":")
                if   len(pts) == 2: cfg["preset_ms"] = (int(pts[0]) * 60 + int(pts[1])) * 1000
                elif len(pts) == 3: cfg["preset_ms"] = (int(pts[0]) * 3600 + int(pts[1]) * 60 + int(pts[2])) * 1000
            elif raw:
                cfg["preset_ms"] = max(1000, int(float(raw) * 1000))
        except: pass
        delay = 0

    if "size" in p:
        selectfont(p["size"])
        rebuild_display()
        delay = 0
    if "scale" in p:
        cfg["scale"] = int(p["scale"])
        rebuild_display()
        delay = 0
    if "mode" in p:
        cfg["mode"] = p["mode"]
        rebuild_display()
        delay = 0
    for k in _INT_PARAMS:
        if k in p:
            cfg[k] = int(p[k])
            delay = 0
    for k in _HEX_PARAMS:
        if k in p:
            cfg[k] = "#" + p[k]
            apply_colors()
            delay = 0
    for k in _ANALOG_RESET:
        if k in p:
            cfg[k] = int(p[k])
            _last_analog = ""
            delay = 0
    if "rainbow" in p:
        cfg["rainbow"] = int(p["rainbow"])
        if not cfg["rainbow"]:
            apply_colors()
        delay = 0
    if "show_temp" in p:
        cfg["show_temp"] = int(p["show_temp"])
        if cfg["show_temp"] and cfg.get("city", ""):
            try: temp_string = fetch_temperature()
            except: pass
        delay = 0
    if "city" in p:
        cfg["city"] = p["city"]
        if cfg["show_temp"] and cfg["city"]:
            try: temp_string = fetch_temperature()
            except: pass
        delay = 0
    return (200, {}, "ok")

def update_datetime():
    with pool.socket() as s:
        s.settimeout(5)
        s.connect(("data.t-skylt.se", 89))
        s.sendall(b"GET / HTTP/1.0\r\nHost: data.t-skylt.se\r\n\r\n")
        buf = bytearray(512)
        n = s.recv_into(buf)
        raw = buf[:n].decode("utf-8")
    # Extract full Date header: "Date: Sat, 22 Mar 2026 15:30:45 GMT"
    datestr = raw.split("Date:", 1)[1].split("\r\n")[0].strip()
    # datestr: "Sat, 22 Mar 2026 15:30:45 GMT"
    day_name = datestr[0:3]
    day_num = datestr[5:7]
    month = datestr[8:11]
    time_str = datestr[17:25]
    hour = str(int(time_str[0:2]))
    minute = str(int(time_str[3:5]))
    second = str(int(time_str[6:8]))
    if len(hour) == 1: hour = "0" + hour
    if len(minute) == 1: minute = "0" + minute
    if len(second) == 1: second = "0" + second
    return (hour, minute, second, day_name, day_num + " " + month)

def fetch_temperature():
    try:
        city = cfg.get("city", "")
        if not city: return ""
        response = requests.get("http://wttr.in/" + city.replace(" ", "+") + "?format=%t")
        data = response.text
        response.close()
        if data:
            temp = str(data).strip()
            clean = ""
            for c in temp:
                if c in "+-0123456789cf ":
                    clean += c
            return clean.strip()
    except:
        pass
    return ""

screen = None
BOX_PAD = 2
_last_tstr = ""

def draw_rounded_box(bmp, x, y, w, h, border, fill):
    bitmaptools.fill_region(bmp, x + 1, y + 1, x + w - 1, y + h - 1, fill)
    for px in range(x + 1, x + w - 1):
        bmp[px, y] = border
        bmp[px, y + h - 1] = border
    for py in range(y + 1, y + h - 1):
        bmp[x, py] = border
        bmp[x + w - 1, py] = border

# --- Analog clock ---
_TWO_PI = 2.0 * math.pi

def _angle(value, total):
    return (value / total) * _TWO_PI - math.pi / 2.0

def _draw_hand(bmp, cx, cy, angle, length, cidx, thick=False):
    ex = int(cx + math.cos(angle) * length + 0.5)
    ey = int(cy + math.sin(angle) * length + 0.5)
    bitmaptools.draw_line(bmp, cx, cy, ex, ey, cidx)
    if thick:
        dx = int(math.cos(angle + math.pi / 2.0) + 0.5)
        dy = int(math.sin(angle + math.pi / 2.0) + 0.5)
        bitmaptools.draw_line(bmp, cx + dx, cy + dy, ex, ey, cidx)
        bitmaptools.draw_line(bmp, cx - dx, cy - dy, ex, ey, cidx)

def _draw_circle_outline(bmp, cx, cy, r, cidx):
    x = 0
    y = r
    d = 3 - 2 * r
    while x <= y:
        for px, py in [(cx+x,cy+y),(cx-x,cy+y),(cx+x,cy-y),(cx-x,cy-y),
                        (cx+y,cy+x),(cx-y,cy+x),(cx+y,cy-x),(cx-y,cy-x)]:
            if 0 <= px < bmp.width and 0 <= py < bmp.height:
                bmp[px, py] = cidx
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1

_last_analog = ""

def _info_line():
    """The small text line under/beside the hands or digits: weekday/date/
    temperature for the clock function, current run state otherwise."""
    if cfg["function"] != "clock":
        return [_STATE_LABELS[sw_state]]
    parts = []
    if cfg["show_day"]: parts.append(day_name)
    if cfg["show_date"]: parts.append(date_str)
    if cfg["show_temp"] and temp_string: parts.append(temp_string)
    return parts

def draw_analog_rect(h, m, s):
    global _last_analog
    tag = str(h) + ":" + str(m) + ":" + str(s)
    if tag == _last_analog:
        return
    _last_analog = tag
    pad = 2
    cx = DISP_W // 2
    cy = DISP_H // 2
    hw = DISP_W // 2 - pad
    hh = DISP_H // 2 - pad
    bitmaptools.fill_region(screen, 0, 0, DISP_W, DISP_H, 14)
    if cfg["show_border"]:
        bitmaptools.draw_line(screen, pad, pad, DISP_W - pad - 1, pad, 13)
        bitmaptools.draw_line(screen, pad, DISP_H - pad - 1, DISP_W - pad - 1, DISP_H - pad - 1, 13)
        bitmaptools.draw_line(screen, pad, pad, pad, DISP_H - pad - 1, 13)
        bitmaptools.draw_line(screen, DISP_W - pad - 1, pad, DISP_W - pad - 1, DISP_H - pad - 1, 13)
    if cfg["show_dots"]:
        for i in range(12):
            a = _angle(i, 12)
            cos_a = math.cos(a)
            sin_a = math.sin(a)
            tx = hw / abs(cos_a) if abs(cos_a) > 0.001 else 9999
            ty = hh / abs(sin_a) if abs(sin_a) > 0.001 else 9999
            t = min(tx, ty)
            dx = max(0, min(DISP_W - 1, int(cx + cos_a * t + 0.5)))
            dy = max(0, min(DISP_H - 1, int(cy + sin_a * t + 0.5)))
            screen[dx, dy] = 18
    R = min(hw, hh)
    h12 = (h % 12) + m / 60.0
    ha = _angle(h12, 12)
    ma = _angle(m, 60)
    _draw_hand(screen, cx, cy, ha, int(R * 0.5), 15, thick=True)
    _draw_hand(screen, cx, cy, ma, int(R * 0.8), 16, thick=True)
    sec_a = _angle(s, 60)
    _draw_hand(screen, cx, cy, sec_a, int(R * 0.9), 17, thick=False)
    screen[cx, cy] = 5
    if cfg["function"] == "countdown" and int(cfg["preset_ms"]) > 0:
        draw_progress_bar(_now_ms(), int(cfg["preset_ms"]))

def draw_analog(h, m, s):
    global _last_analog
    tag = str(h) + ":" + str(m) + ":" + str(s)
    if tag == _last_analog:
        return
    _last_analog = tag
    R = min(DISP_W, DISP_H) // 2 - 2
    # on short displays (32px), left-align the clock face; otherwise center
    if DISP_H <= 32 and DISP_W > DISP_H:
        cx = R + 2
    else:
        cx = DISP_W // 2
    cy = DISP_H // 2
    bitmaptools.fill_region(screen, 0, 0, DISP_W, DISP_H, 14)
    if cfg["show_border"]:
        _draw_circle_outline(screen, cx, cy, R, 13)
    # 5-minute tick marks (12 dots, 1px, on the circle edge)
    if cfg["show_dots"]:
        for i in range(12):
            a = _angle(i, 12)
            tx = int(cx + math.cos(a) * R + 0.5)
            ty = int(cy + math.sin(a) * R + 0.5)
            if 0 <= tx < DISP_W and 0 <= ty < DISP_H:
                screen[tx, ty] = 18
    # hands
    h12 = (h % 12) + m / 60.0
    ha = _angle(h12, 12)
    ma = _angle(m, 60)
    _draw_hand(screen, cx, cy, ha, int(R * 0.5), 15, thick=True)
    _draw_hand(screen, cx, cy, ma, int(R * 0.8), 16, thick=True)
    sa = _angle(s, 60)
    _draw_hand(screen, cx, cy, sa, int(R * 0.85), 17, thick=False)
    # center dot
    screen[cx, cy] = 5
    # on short displays, draw info text to the right of the clock face
    if DISP_H <= 32 and DISP_W > DISP_H:
        # vertical accent separator
        if cfg["accent"]:
            sep_x = cx + R + 3
            if 0 <= sep_x < DISP_W:
                bitmaptools.draw_line(screen, sep_x, 1, sep_x, DISP_H - 2, 19)
            text_x = sep_x + 3
        else:
            text_x = cx + R + 4
        ty = 2
        for part in _info_line():
            if text_x < DISP_W and ty + 5 <= DISP_H:
                _render_dim_text(part, text_x, ty)
                ty += 8
    if cfg["function"] == "countdown" and int(cfg["preset_ms"]) > 0:
        draw_progress_bar(_now_ms(), int(cfg["preset_ms"]))

def draw_progress_bar(ms, total):
    """Bottom 3px bar showing time remaining -- countdown + digital/analog
    alike, drawn last so it's never erased by the fill underneath it."""
    remain = max(0, total - ms)
    bar_w  = int(DISP_W * remain // total) if total > 0 else 0
    bar_y  = DISP_H - 3
    bitmaptools.fill_region(screen, 0, bar_y, DISP_W, DISP_H, 11)
    if bar_w > 0:
        bitmaptools.fill_region(screen, 0, bar_y, bar_w, DISP_H, 19)

def rebuild_display():
    global screen, _last_tstr, _last_analog
    screen = displayio.Bitmap(DISP_W, DISP_H, 20)
    tg = displayio.TileGrid(screen, pixel_shader=palette)
    root = displayio.Group()
    root.append(tg)
    display.root_group = root
    apply_colors()
    _last_tstr = ""
    _last_analog = ""
    gc.collect()

def draw_time(timestring, colon_vis=True):
    global _last_tstr
    # Internal early-return cache: lets the main loop call this every tick
    # (needed for stopwatch tenths-of-a-second precision) while an
    # unchanged clock display (gated externally to ~once/sec) still only
    # costs one cheap string compare per call, not a full redraw.
    tag = timestring + str(colon_vis)
    if tag == _last_tstr:
        return
    _last_tstr = tag

    f = load_screen.currentfont
    fh = f["fontheight"]
    requested_scale = cfg.get("scale", 1)

    # build display string with optional colon blink
    dstr = timestring
    colon_blank = BLANK * f.get(":", (3,))[0]  # pixel-width placeholder for hidden colon
    if cfg["blink_colon"] and not colon_vis:
        dstr = dstr.replace(":", colon_blank)

    # 12h conversion for display -- only meaningful for actual wall-clock time
    ampm = ""
    if cfg["function"] == "clock" and cfg["h12"]:
        parts = timestring.split(":")
        h24 = int(parts[0])
        ampm = "am" if h24 < 12 else "pm"
        h12 = h24 % 12
        if h12 == 0: h12 = 12
        hstr = str(h12)
        if cfg["blink_colon"] and not colon_vis:
            dstr = hstr + colon_blank + parts[1] if len(parts) == 2 else hstr + colon_blank + parts[1] + colon_blank + parts[2]
        else:
            dstr = hstr + ":" + parts[1] if len(parts) == 2 else hstr + ":" + parts[1] + ":" + parts[2]
        # reference string for stable box: widest 12h is "12:88" or "12:88:88"
        ref = "12:" + parts[1] if len(parts) == 2 else "12:" + parts[1] + ":" + parts[2]
    else:
        # reference string: always use colons for stable width
        ref = timestring

    tw = strlen(dstr, f)
    ref_w = strlen(ref, f)
    tmp = displayio.Bitmap(tw + 2, fh + 2, 20)
    _shadow = cfg.get("show_shadow", 1)
    pprint(dstr, 0, font=f, clear=False, color="white",
           top_offset=-1, _refresh=False, window=tmp, _clearscreen=False,
           block=bool(_shadow), shadow_color=12)

    info_parts = _info_line()
    if cfg["function"] == "clock" and ampm:
        info_parts = info_parts + [ampm]
    info_str = " . ".join(info_parts) if info_parts else ""
    info_h = 6 if info_str else 0
    accent_gap = 3 if cfg["accent"] else 0

    # Fit the visible glyphs, not the temporary bitmap's 2px padding.
    max_time_h = max(1, DISP_H - info_h - accent_gap - 2)
    scale = max(1, requested_scale)
    shadow_pad = scale if _shadow else 0
    while scale > 1 and (ref_w * scale + shadow_pad > DISP_W or fh * scale + shadow_pad > max_time_h):
        scale -= 1
        shadow_pad = scale if _shadow else 0
    sw = ref_w * scale + shadow_pad
    sh = fh * scale + shadow_pad
    total_h = sh + info_h + accent_gap
    time_y = max((DISP_H - total_h) // 2, 0)

    bitmaptools.fill_region(screen, 0, 0, DISP_W, DISP_H, 14)

    if scale == 1:
        tx = max((DISP_W - tw) // 2, 0)
        bitmaptools.blit(screen, tmp, tx, time_y,
                         x1=0, y1=0, x2=tmp.width, y2=tmp.height,
                         skip_source_index=0)
    else:
        bitmaptools.rotozoom(screen, tmp,
                             ox=DISP_W // 2, oy=time_y + (tmp.height // 2) * scale,
                             px=tmp.width // 2, py=tmp.height // 2,
                             angle=0.0, scale=float(scale),
                             skip_index=0)

    if cfg["accent"]:
        ay = time_y + sh + 1
        if ay < DISP_H:
            line_w = min(max(sw // 3, 8), DISP_W - 4)
            ax = (DISP_W - line_w) // 2
            bitmaptools.fill_region(screen, ax, ay, ax + line_w, min(ay + 1, DISP_H), 19)

    if info_str:
        iy = time_y + sh + accent_gap
        iw = strlen(info_str, font_mini)
        ix = max((DISP_W - iw) // 2, 0)
        if iy + 5 <= DISP_H:
            info_tmp = displayio.Bitmap(iw + 1, 6, 20)
            pprint(info_str, 0, font=font_mini, clear=False, color="white",
                   top_offset=-1, _refresh=False, window=info_tmp, _clearscreen=False)
            # dim the info: swap palette 5 pixels to 18
            for py in range(info_tmp.height):
                for px in range(info_tmp.width):
                    if info_tmp[px, py] == 5:
                        info_tmp[px, py] = 18
            bitmaptools.blit(screen, info_tmp, ix, iy,
                             x1=0, y1=0, x2=info_tmp.width, y2=info_tmp.height,
                             skip_source_index=0)

    if cfg["function"] == "countdown" and int(cfg["preset_ms"]) > 0:
        draw_progress_bar(_now_ms(), int(cfg["preset_ms"]))

dt = update_datetime()
hour, minute, second = dt[0], dt[1], dt[2]
day_name, date_str = dt[3], dt[4]
temp_string = ""
weather_counter = 0

# anchor NTP time to monotonic clock for accurate seconds
_sync_epoch = int(hour) * 3600 + int(minute) * 60 + int(second)
_sync_mono = time.monotonic()
_last_resync = _sync_mono

if cfg["show_temp"] and cfg.get("city", ""):
    try: temp_string = fetch_temperature()
    except: pass

rebuild_display()

_rainbow_hue = 0

while load_settings.app_running:
    ampule.listen(socket)

    b = check_if_button_pressed()
    if b == 2: sys.exit()
    if b == 1 and cfg["function"] != "clock": _toggle()

    now_mono = time.monotonic()

    if cfg["function"] == "clock":
        # derive current time from monotonic offset
        elapsed = now_mono - _sync_mono
        epoch = _sync_epoch + int(elapsed)
        # handle day rollover
        if epoch >= 86400:
            epoch = epoch % 86400
        h = epoch // 3600
        m = (epoch % 3600) // 60
        s = epoch % 60

        hour = ("0" + str(h)) if h < 10 else str(h)
        minute = ("0" + str(m)) if m < 10 else str(m)
        second = ("0" + str(s)) if s < 10 else str(s)

        # re-sync with NTP every 5 minutes to prevent drift
        if now_mono - _last_resync > 300:
            try:
                dt = update_datetime()
                hour, minute, second = dt[0], dt[1], dt[2]
                day_name, date_str = dt[3], dt[4]
                _sync_epoch = int(hour) * 3600 + int(minute) * 60 + int(second)
                _sync_mono = now_mono
                _last_resync = now_mono
            except:
                _last_resync = now_mono

        # weather refresh every 10 minutes
        if cfg["show_temp"] and int(elapsed) % 600 < 2 and s < 2:
            if weather_counter == 0:
                weather_counter = 1
                try: temp_string = fetch_temperature()
                except: pass
        elif s >= 2:
            weather_counter = 0

        if cfg["show_seconds"]:
            timestring = hour + ":" + minute + ":" + second
        else:
            timestring = hour + ":" + minute

        # rainbow color cycling
        if cfg["rainbow"] and cfg["mode"] == "digital":
            _rainbow_hue = (_rainbow_hue + 3) % 360
            rgb = _hsv_to_rgb(_rainbow_hue)
            palette[5] = rgb
            palette[12] = (rgb[0] // 4, rgb[1] // 4, rgb[2] // 4)
            palette[18] = (rgb[0] // 3, rgb[1] // 3, rgb[2] // 3)
            _last_tstr = ""  # force redraw

        # colon blink — toggle every half second
        colon_vis = int(now_mono * 2) % 2 == 0
        ih, im, isec = int(hour), int(minute), int(second)

        if cfg["mode"] == "analog":
            draw_analog(ih, im, isec)
        elif cfg["mode"] == "analog_rect":
            draw_analog_rect(ih, im, isec)
        else:
            draw_time(timestring, colon_vis)

    else:  # stopwatch / countdown
        ms = _now_ms()
        if cfg["function"] == "countdown" and sw_state == SW_RUNNING and ms >= int(cfg["preset_ms"]):
            sw_elapsed_ms = int(cfg["preset_ms"])
            sw_state      = SW_FINISHED
            ms = sw_elapsed_ms

        disp_ms = max(0, int(cfg["preset_ms"]) - ms) if cfg["function"] == "countdown" else ms

        # flash the digits/center-dot (palette 5) while a countdown is done,
        # same visual cue the old /stopwatch app used
        if sw_state == SW_FINISHED:
            flash = int(now_mono * 2) % 2
            palette[5] = hex_to_rgb(cfg["accent_hex"]) if flash else hex_to_rgb(cfg["f_hex"])

        total_s = disp_ms // 1000
        tenth   = (disp_ms % 1000) // 100
        th = total_s // 3600
        tm = (total_s % 3600) // 60
        ts = total_s % 60
        mm = ("0" + str(tm))[-2:]
        ss = ("0" + str(ts))[-2:]

        if cfg["mode"] == "analog":
            draw_analog(th, tm, ts)
        elif cfg["mode"] == "analog_rect":
            draw_analog_rect(th, tm, ts)
        else:
            if th > 0:
                dstr = str(th) + ":" + mm + ":" + ss
            elif cfg["show_tenths"]:
                dstr = mm + ":" + ss + "." + str(tenth)
            else:
                dstr = mm + ":" + ss
            draw_time(dstr, True)

    refresh()
    time.sleep(0.05)
